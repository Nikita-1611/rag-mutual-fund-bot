import os
import json
import logging
from dotenv import load_dotenv
from pinecone import Pinecone

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # RAG directory
INPUT_FILE = os.path.join(ROOT_DIR, "..", "output", "embedded", "vector_payloads.json")
# Load .env variables
load_dotenv(os.path.join(ROOT_DIR, "..", ".env"))

INDEX_NAME = "mutual-fund-faq"

def run_indexing():
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}. Please run Phase 3 first.")
        return

    logger.info(f"Loading vector payloads from {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        payloads = json.load(f)

    if not payloads:
        logger.warning("No payloads found to index.")
        return
        
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key or "your_pinecone_api_key_here" in api_key:
        logger.error("PINECONE_API_KEY is not configured in .env")
        return

    logger.info(f"Connecting to Pinecone...")
    pc = Pinecone(api_key=api_key)
    
    # Connect to the target index
    index = pc.Index(INDEX_NAME)
    
    # Prepare data for upload: Pinecone needs tuples or dicts of (id, values, metadata)
    records = []
    
    for item in payloads:
        # Pinecone vector format {"id": str, "values": list[float], "metadata": dict}
        records.append({
            "id": item["chunk_id"],
            "values": item["embedding"],
            "metadata": item["metadata"]
        })
        
    # Batch Upload to Pinecone (Max batch size usually 100-200)
    BATCH_SIZE = 100
    total_chunks = len(records)
    
    logger.info(f"Starting upsert of {total_chunks} records into Pinecone index '{INDEX_NAME}'...")
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        
        logger.info(f"Upserting batch {i} to {min(i+BATCH_SIZE, total_chunks)}...")
        index.upsert(vectors=batch)

    logger.info(f"Phase 4 Complete. All {total_chunks} chunks pushed to Pinecone.")

if __name__ == "__main__":
    logger.info("Starting Phase 4 Indexing Job (Pinecone)...")
    run_indexing()
