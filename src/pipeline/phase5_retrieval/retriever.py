import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# from huggingface_hub import InferenceClient # Removed for Cohere unification
from pinecone import Pinecone
import cohere
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import sys

# Add phases to path safely so we can import them
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from phase7_generation.validator import ConstraintValidator
from phase6_security.guardrails import GuardrailEngine

# Setup Logging
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # RAG directory
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Check for Tracing Status
if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
    logger.info("LangSmith Tracing: ENABLED")
else:
    logger.info("LangSmith Tracing: DISABLED (Set LANGCHAIN_TRACING_V2=true and provide API key to enable)")

INDEX_NAME = "mutual-fund-faq"

# Prompt template enforcing strict facts-only constraint
PROMPT_TEMPLATE = """
System: You are the core analytical engine for the Mutual Fund FAQ Assistant.
You operate under the following absolute constraints:
1. You may ONLY output facts explicitly present in the provided Context.
2. If the context does not contain the answer, you must output EXACTLY: "I do not have this factual information in my current corpus."
3. NO prediction. NO investment advice. NO mathematical evaluations or forecasts.
4. Your response must be <= 3 sentences.

Context:
{context}

Question:
{question}
"""

# Prompt for query rewriting based on session history
REWRITE_PROMPT = """
System: You are a Query Rewriter for a Mutual Fund AI. 
Your task is to rewrite the User Question into a standalone, complete factual question based on the Conversation History.

CRITICAL RULES:
1. OUTPUT ONLY THE REWRITTEN QUESTION.
2. NO conversational filler, NO preamble (e.g., "Here is the rewritten question"), NO explanations.
3. If the User Question is already standalone, return it exactly as is.
4. Replace pronouns (it, its, their, this fund, that one) with the specific fund name mentioned in history.
5. KEEP IT CONCISE AND FACTUAL.

### Examples:
- History: User: Tell me about SBI Bluechip. Assistant: SBI Bluechip is...
  User Question: What is its exit load?
  Standalone Question: What is the exit load of SBI Bluechip Fund?

- History: User: What is Quant Small Cap? Assistant: Quant Small Cap is...
  User Question: How has this fund performed?
  Standalone Question: How has the Quant Small Cap Fund performed?

- History: User: What is a SIP? Assistant: SIP stands for...
  User Question: How to start one?
  Standalone Question: How to start a Systematic Investment Plan (SIP)?

### Current Task:
History:
{history}

User Question: {question}
Standalone Question:"""

class RAGRetriever:
    def __init__(self):
        # 1. Initialize Pinecone
        pc_api = os.environ.get("PINECONE_API_KEY")
        if not pc_api or "your_pinecone_api" in pc_api:
            raise ValueError("Missing PINECONE_API_KEY")
        self.pc = Pinecone(api_key=pc_api)
        self.index = self.pc.Index(INDEX_NAME)

        # 2. API-based Embedder (Unified under Cohere)
        # Using embed-english-light-v3.0 (384 dimensions)
        logger.info("Using Cohere for unified embeddings and re-ranking...")
        # (co_client is initialized below in Step 3)

        # 3. Initialize Cohere for Cross-Encoder Re-Ranking
        cohere_api = os.environ.get("COHERE_API_KEY")
        if not cohere_api or "your_cohere_api" in cohere_api:
            raise ValueError("Missing COHERE_API_KEY")
        self.co_client = cohere.Client(api_key=cohere_api)

        # 4. Initialize Gemini 1.5 Flash Generator via Google AI
        google_api = os.environ.get("GOOGLE_API_KEY")
        if not google_api:
            logger.error("GOOGLE_API_KEY environment variable not set.")
            raise ValueError("Missing GOOGLE_API_KEY")
        
        # Robust LLM Initialization (v1 REST Stack)
        # Forcing v1 version and rest transport to bypass v1beta 404 errors on Render.
        self.google_api_key = google_api
        self.fallback_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        
        # Initialize primary LLM with stable production settings
        self.llm = ChatGoogleGenerativeAI(
            model=self.fallback_models[0], 
            temperature=0.0, 
            google_api_key=self.google_api_key,
            max_retries=2,
            version="v1",
            transport="rest",
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        
        # 5. Initialize Phase 6 Guardrail Pre-Flight Security Engine (Keyword-based)
        self.guardrails = GuardrailEngine()
        
    def _rewrite_query(self, user_question: str, history: List[Dict[str, str]]) -> str:
        """
        Uses Gemini 1.5 Flash to rewrite follow-up questions into standalone queries.
        """
        if not history:
            return user_question
            
        logger.info("Rewriting query based on session history...")
        history_str = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history[-5:]])
        
        prompt = PromptTemplate(template=REWRITE_PROMPT, input_variables=["history", "question"])
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({"history": history_str, "question": user_question})
            rewritten = response.content.strip()
            
            # Robust cleaning to remove common LLM prefixes/chatter if they leak through
            # 1. Take first line only
            rewritten = rewritten.split("\n")[0].strip()
            # 2. Remove common headers the LLM might include
            for prefix in ["Standalone Question:", "Question:", "Rewritten Question:", "Rewritten:", "Standalone:"]:
                 if rewritten.lower().startswith(prefix.lower()):
                     rewritten = rewritten[len(prefix):].strip()
            
            # 3. Remove surrounding quotes
            rewritten = rewritten.strip('"').strip("'")
            
            logger.info(f"Original: '{user_question}' -> Rewritten: '{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"Query rewriting failed: {e}")
            return user_question

    def query(self, user_question: str, history: List[Dict[str, str]] = []) -> dict:
        logger.info(f"Received query: '{user_question}' (History depth: {len(history)})")
        
        # Step 0: Rewrite query if history exists
        standalone_question = self._rewrite_query(user_question, history)
        
        # Security Gate 0: Phase 6 Intent & PII Refusal Engine
        logger.info("Running pre-flight Security Sweeps...")
        is_safe, refusal_msg = self.guardrails.validate_query(standalone_question)
        if not is_safe:
            return {
                "answer": refusal_msg,
                "source_url": "N/A",
                "last_updated": "N/A",
                "is_refusal": True
            }
            
        # Step 1: Embed Query (via Cohere API - Pure Python)
        logger.info("Embedding the query via Cohere API...")
        try:
            response = self.co_client.embed(
                texts=[standalone_question],
                model='embed-english-light-v3.0',
                input_type='search_query',
                embedding_types=['float']
            )
            query_vector = response.embeddings.float[0]
                 
            if not query_vector:
                raise ValueError("Cohere returned an empty embedding vector.")
                
        except Exception as e:
            logger.exception(f"Cohere Embedding API failed: {e}")
            return {
                "answer": "External Connectivity Error: The embedding service (Cohere) is currently unavailable or unauthorized. Please check your COHERE_API_KEY.",
                "source_url": "N/A",
                "last_updated": "N/A",
                "is_refusal": True,
                "is_error": True
            }
        
        # Step 2: Hybrid/Dense Search on Pinecone
        logger.info("Fetching Top-15 semantic candidates from Pinecone...")
        try:
            search_results = self.index.query(
                vector=query_vector,
                top_k=15,
                include_metadata=True
            )
            matches = search_results.get("matches", [])
        except Exception as e:
            logger.exception(f"Pinecone query failed: {e}")
            return {
                "answer": "External Connectivity Error: The vector database (Pinecone) is currently unreachable.",
                "source_url": "N/A",
                "last_updated": "N/A",
                "is_refusal": True,
                "is_error": True
            }
        
        # Reject chunks if the top match score is below 0.55 
        # (prevents hallucinating "close enough" but incorrect data)
        # Note: Adjusted to 0.55 to capture specific factual matches (e.g. lock-in)
        if not matches or (matches[0].get("score", 0) < 0.55):
            logger.warning(f"Low confidence retrieval (Score: {matches[0].get('score', 0) if matches else 0}). Returning fallback.")
            return {
                "answer": "I do not have this factual information in my current corpus.",
                "source_url": "N/A",
                "last_updated": "N/A"
            }

        # Step 3: Re-Rank Top 15 to Top 3 using Cohere
        logger.info("Re-Ranking candidates via Cohere Cross-Encoder...")
        documents = [match["metadata"]["text"] for match in matches if "text" in match["metadata"]]
        urls = [match["metadata"]["source_url"] for match in matches if "source_url" in match["metadata"]]
        dates = [match["metadata"]["last_updated"] for match in matches if "last_updated" in match["metadata"]]
        
        # Guardrail against empty documents payload
        if not documents:
             return {
                "answer": "Missing text metadata. I do not have this factual information in my current corpus.",
                "source_url": "N/A",
                "last_updated": "N/A"
            }

        try:
            reranked = self.co_client.rerank(
                model='rerank-english-v3.0',
                query=standalone_question,
                documents=documents,
                top_n=3
            )
            top_3_indices = [result.index for result in reranked.results]
        except Exception as e:
            logger.exception(f"Cohere rerank failed: {e}")
            # Fallback to top-3 from Pinecone if Cohere fails, rather than crashing
            top_3_indices = [0, 1, 2][:len(documents)]
        
        # Build strict context string
        context_chunks = []
        best_url = urls[top_3_indices[0]] if top_3_indices and len(urls) > top_3_indices[0] else "URL Unavailable"
        
        for idx in top_3_indices:
            context_chunks.append(documents[idx])
            
        context_str = "\n\n---\n\n".join(context_chunks)
        
        # Step 4: Generate Response via resilient LLM loop
        logger.info("Passing top 3 re-ranked contexts to LLM constraint generator...")
        prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
        
        last_error = ""
        for model_name in self.fallback_models:
            try:
                # Update model for this attempt
                self.llm.model = model_name
                logger.info(f"Attempting generation with model: {model_name}")
                
                chain = prompt | self.llm
                response = chain.invoke({"context": context_str, "question": user_question})
                output_text = response.content.strip()
                
                # If we got here, success!
                break
            except Exception as e:
                last_error = str(e)
                if "404" in last_error or "not found" in last_error.lower():
                    logger.warning(f"Model {model_name} not found. Trying next fallback...")
                    continue
                else:
                    # Non-404 error (Auth, Quota), log and return immediately
                    logger.error(f"Gemini critical error ({model_name}): {last_error}")
                    return {
                        "answer": f"External Connectivity Error: Google Gemini is currently unreachable. Reason: {last_error}",
                        "source_url": "N/A",
                        "last_updated": "N/A",
                        "is_refusal": True,
                        "is_error": True
                    }
        else:
            # All fallbacks failed
            return {
                "answer": f"External Connectivity Error: No supported Gemini models were found for your API key. (Last error: {last_error})",
                "source_url": "N/A",
                "last_updated": "N/A",
                "is_refusal": True,
                "is_error": True
            }
        
        # Execute Phase 7 Post-Processing Constraint Validation
        # If the LLM returns the explicit refusal string, we skip citations
        if "I do not have this factual information" in output_text:
            return {
                "answer": output_text,
                "source_url": "N/A",
                "last_updated": "N/A"
            }
        
        best_date = dates[top_3_indices[0]] if top_3_indices and len(dates) > top_3_indices[0] else ""
        
        # Delegate mapping constraints explicitly to the Phase 7 Validation Gatekeeper
        final_payload = ConstraintValidator.format_final_payload(
            raw_llm_text=output_text,
            source_url=best_url,
            last_updated=best_date
        )
        return final_payload

if __name__ == "__main__":
    # Internal Unit Test
    logger.info("Initializing Unit Test for Phase 5 Retrieval Pipeline...")
    try:
        retriever_engine = RAGRetriever()
        sample_q = "What is the exit load for the SBI ELSS tax saver fund?"
        answer = retriever_engine.query(sample_q)
        print("\n================ FINAL RESPONSE ================\n")
        print(answer)
        print("\n================================================")
    except Exception as e:
        logger.error(f"Error initializing test: {e}")
