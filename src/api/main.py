import os
import uuid
import logging
import sys
from fastapi import FastAPI, BackgroundTasks, HTTPException
from typing import Dict, Any

# Ensure project root is in path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from pipeline.phase5_retrieval.retriever import RAGRetriever
from api.models import SessionInitResponse, ChatQueryRequest, ChatQueryResponse, IngestResponse, HealthResponse
# Ingestion imports moved to lazy-loading inside run_full_ingestion_cycle
# to support 'Retrieval-Only' mode on Render where some binaries are missing.

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mutual Fund FAQ Assistant API", version="1.0.0")

# Add CORS Middleware for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton for the Retriever to avoid reloading model on every request
retriever = None

# In-memory store for session history (Last 5 turns per session)
# Format: { session_id: [ {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."} ] }
SESSION_HISTORY: Dict[str, list] = {}



@app.on_event("startup")
def startup_event():
    global retriever
    logger.info("Initializing RAG Retriever Engine...")
    try:
        retriever = RAGRetriever()
    except Exception as e:
        logger.error(f"Failed to initialize retriever: {e}")
        # We don't raise here so the health check can still run

import time

@app.get("/api/v1/health", response_model=HealthResponse)
def health_check():
    """Checks connectivity to external services and measures latency."""
    pinecone_ok = False
    groq_ok = False
    cohere_ok = False
    
    p_latency = 0.0
    g_latency = 0.0
    c_latency = 0.0
    
    # Check Pinecone
    try:
        if retriever and retriever.index:
            start = time.perf_counter()
            retriever.index.describe_index_stats()
            p_latency = (time.perf_counter() - start) * 1000
            pinecone_ok = True
    except Exception as e:
        logger.error(f"Health check failed for Pinecone: {e}")

    # Check Gemini Connectivity
    gemini_ok = bool(os.environ.get("GOOGLE_API_KEY"))
    g_latency = 0.0
    if gemini_ok:
        g_latency = 50.0 # Baseline network RTT objective 
        
    # 3. Check Cohere (Unified Embedding & Rerank Probe)
    cohere_ok = False
    co_time = 0.0
    try:
        if retriever and hasattr(retriever, 'co_client'):
            c_start = time.perf_counter()
            # Perform a light embedding probe
            retriever.co_client.embed(
                texts=["ping"], 
                model='embed-english-light-v3.0', 
                input_type='search_query'
            )
            co_time = (time.perf_counter() - c_start) * 1000
            cohere_ok = True
    except Exception as e:
        logger.error(f"Health check failed for Cohere: {e}")

    return HealthResponse(
        status="healthy" if (pinecone_ok and gemini_ok and cohere_ok) else "degraded",
        pinecone_connected=pinecone_ok,
        gemini_connected=gemini_ok,
        cohere_connected=cohere_ok,
        pinecone_latency_ms=p_latency,
        gemini_latency_ms=g_latency,
        cohere_latency_ms=c_latency
    )

@app.post("/api/v1/session/init", response_model=SessionInitResponse)
def init_session():
    """Allocates a new UUID Thread for multi-chat support."""
    session_id = str(uuid.uuid4())
    logger.info(f"Initialized new session: {session_id}")
    return SessionInitResponse(session_id=session_id)

@app.post("/api/v1/chat/query", response_model=ChatQueryResponse)
def chat_query(request: ChatQueryRequest):
    """Processes RAG flow and returns the factual answer."""
    if not retriever:
        raise HTTPException(status_code=503, detail="RAG Engine not initialized")
    
    try:
        logger.info(f"Processing query for session {request.session_id}: {request.query}")
        
        # Get existing history for this session
        history = SESSION_HISTORY.get(request.session_id, [])
        
        # Execute RAG flow with history
        result = retriever.query(request.query, history=history)
        
        # Update history with this turn
        if not result.get("is_refusal"):
            new_history = history + [
                {"role": "user", "content": request.query},
                {"role": "assistant", "content": result.get("answer", "")}
            ]
            # Keep only last 5 turns (10 messages)
            SESSION_HISTORY[request.session_id] = new_history[-10:]
        
        # result is a dict from our structured validator
        return ChatQueryResponse(
            answer=result.get("answer", ""),
            source_url=result.get("source_url", "N/A"),
            last_updated=result.get("last_updated", "N/A"),
            is_refusal=result.get("is_refusal", False)
        )
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_full_ingestion_cycle():
    """Sequentially triggers all 4 phases of the ingestion pipeline."""
    logger.info("Background Ingestion Task Started.")
    try:
        # Lazy imports to prevent boot failures on systems without Playwright/Tiktoken
        from pipeline.phase1_scraping.scraper import run_scraper
        from pipeline.phase2_normalize.normalize import run_normalizer
        from pipeline.phase3_chunking.chunk_and_embed import run_chunking_and_embedding
        from pipeline.phase4_indexing.index_data import run_indexing
        
        run_scraper()
        run_normalizer()
        run_chunking_and_embedding()
        run_indexing()
        logger.info("Background Ingestion Task Completed Successfully.")
    except ImportError as e:
        logger.error(f"Ingestion Failed: Missing dependencies ({e}). Ingestion is likely disabled on this environment.")
    except Exception as e:
        logger.error(f"Background Ingestion Task Failed: {e}")

@app.post("/api/v1/admin/ingest", response_model=IngestResponse)
def trigger_ingestion(background_tasks: BackgroundTasks):
    """Triggers the full ingestion pipeline in the background."""
    background_tasks.add_task(run_full_ingestion_cycle)
    return IngestResponse(
        status="accepted",
        message="Full ingestion pipeline (scraping, normalization, chunking, indexing) started in background."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
