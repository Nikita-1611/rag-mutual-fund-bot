import re
import logging
from typing import Tuple
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)

# Hardcoded compliance strings
REFUSAL_PAYLOAD = "I can only provide verified factual data. For investment advice, please consult a registered advisor. Facts-only. No investment advice.\n\n*Educational Material: https://www.amfiindia.com/investor-corner*"
PII_REFUSAL_PAYLOAD = "Your query was blocked to protect your privacy. Please do not submit PAN, Aadhaar, phone numbers, or email addresses."

INTENT_PROMPT = """
System: You are an extremely strict compliance classifier for a Mutual Fund AI.
Your ONLY job is to classify the user's intent into EXACTLY ONE of two categories:

- "FACTUAL": The user is asking an objective, direct question about a concept, fund mechanism, NAV, exit load, or definition (e.g. "What is an ELSS?", "What is the NAV of SBI fund?").
- "ADVICE": The user is asking for subjective opinions, investment returns, performance comparisons, mathematical calculations, or future projections (e.g. "Should I invest here?", "Is Axis better than SBI?", "What will be my wealth in 5 years?", "How much if I invest 5000 in SIP?").

You must reply with ONLY the word "FACTUAL" or "ADVICE". No other output is permitted.

User Query:
{query}
"""

class GuardrailEngine:
    """
    Executes mandatory pre-flight constraints (Phase 6) to intercept PII and stop
    financial advisory hallucination attempts strictly before Vector DB Retrieval.
    """
    
    def __init__(self, groq_api_key: str):
        # We use a standalone, rapid Groq node for zero-shot classification 
        self.classifier_llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.0, groq_api_key=groq_api_key)
        self.intent_prompt = PromptTemplate(template=INTENT_PROMPT, input_variables=["query"])
        self.chain = self.intent_prompt | self.classifier_llm

    def _sweep_pii(self, query: str) -> bool:
        """
        Runs extremely fast regex patterns to detect PAN, Aadhaar, emails, or phone drops.
        Returns True if PII is detected.
        """
        patterns = [
            r'[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}',          # Indian PAN Profile
            r'\b\d{4}\s?\d{4}\s?\d{4}\b',               # Aadhaar (12 digits, optional spaces)
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', # Standard Email
            r'\b[6-9]\d{9}\b'                           # Indian Phone Numbers
        ]
        
        for pattern in patterns:
            if re.search(pattern, query):
                logger.warning(f"PII Sweep Triggered! Pattern matched: {pattern}")
                return True
        return False

    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Executes the dual-layered check.
        Returns (is_allowed: bool, refusal_string: str)
        """
        # Layer 1: PII Static Sweeps
        if self._sweep_pii(query):
             return False, PII_REFUSAL_PAYLOAD
             
        # Layer 2: Subjective/Advice Intent Classifier
        logger.info("Executing zero-shot Llama-3 Intent Classification...")
        try:
            response = self.chain.invoke({"query": query})
            intent = response.content.strip().upper()
            
            if "ADVICE" in intent:
                logger.warning(f"Compliance Block! User query classified as ADVICE. Blocking payload.")
                return False, REFUSAL_PAYLOAD
            elif "FACTUAL" in intent:
                return True, ""
            else:
                # If model hallucinates formatting, default to safe block
                logger.warning(f"Ambiguous intent classification ('{intent}'). Defaulting to safe block.")
                return False, REFUSAL_PAYLOAD
                
        except Exception as e:
            logger.error(f"Intent Classifier crashed: {e}")
            # Fail closed (Block if security layer crashes)
            return False, REFUSAL_PAYLOAD
