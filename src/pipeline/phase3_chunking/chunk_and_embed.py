import os
import json
import uuid
import logging
import re
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # RAG directory
INPUT_DIR = os.path.join(ROOT_DIR, "..", "output", "normalized")
OUTPUT_DIR = os.path.join(ROOT_DIR, "..", "output", "embedded")

def check_tabular(chunk_text: str) -> bool:
    """Checks if the markdown text chunk contains a table format."""
    return "|---" in chunk_text or "| ---" in chunk_text

def chunk_document(content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Splits document and infuses chunk-level metadata."""
    # Using Tiktoken limits (500 tokens) to ensure size continuity
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-3.5-turbo", # BGE uses standard tokenizer similar to this limit scope
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " "]
    )
    
    # 1. Clean the content of the frontmatter if it's causing noise
    # (Optional, but let's keep the focus on prepending the verified tags)
    clean_content = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            clean_content = parts[2].strip()
            
    raw_chunks = text_splitter.split_text(clean_content)
    processed_chunks = []
    
    # Prepare tags prefix with scheme name for explicit context
    scheme_name = metadata.get("scheme_name", "Mutual Fund")
    tags = metadata.get("fund_tags", [])
    
    # Clean up tags (remove problematic special characters like the corrupted bullet)
    clean_tags = [t.replace("?", " ").replace("•", " ").strip() for t in tags]
    tags_str = ", ".join(clean_tags)
    
    # Create a factual sentence-like prefix
    if tags:
        tags_prefix = f"Information for {scheme_name}: This fund is categorized with the following features and tags: {tags_str}.\n\n"
    else:
        tags_prefix = f"Information for {scheme_name}:\n\n"
    
    for text in raw_chunks:
        chunk_id = str(uuid.uuid4())
        is_tabular = check_tabular(text)
        
        # Prepend explicit context to the text before embedding
        final_text = tags_prefix + text
        
        chunk_payload = {
            "chunk_id": chunk_id,
            "text": final_text,
            "metadata": {
                "source_url": metadata.get("source_url", ""),
                "scheme_name": metadata.get("scheme_name", ""),
                "fund_tags": tags,
                "last_updated": metadata.get("last_updated", ""),
                "is_tabular": is_tabular
            }
        }
        processed_chunks.append(chunk_payload)
        
    return processed_chunks

def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Embeds a batch of chunks using local BAAI bge-small-en-v1.5 model."""
    logger.info("Loading local BAAI/bge-small-en-v1.5 model...")
    # Instantiate the local model
    try:
        model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    except Exception as e:
        logger.error(f"Failed to load sentence_transformers: {str(e)}")
        raise
    
    BATCH_SIZE = 32
    total_chunks = len(chunks)
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        
        logger.info(f"Submitting batch {i} to {min(i+BATCH_SIZE, total_chunks)} for local embedding inference...")
        # encode returns a numpy array, convert to list for JSON serialization
        embeddings = model.encode(texts, normalize_embeddings=True)
        
        # Map embeddings back to chunks
        for j, embedding_array in enumerate(embeddings):
            batch[j]["embedding"] = embedding_array.tolist()
            
    logger.info(f"Successfully vectorized {total_chunks} chunks locally.")
    return chunks

def run_chunking_and_embedding():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(INPUT_DIR):
        logger.warning(f"Input directory not found: {INPUT_DIR}. Please run Phase 2 Normalize first.")
        return

    all_vector_payloads = []
    
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".json")]
    
    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        content = data.get("content", "")
        metadata = data.get("metadata", {})
        
        if not content:
            continue
            
        chunks = chunk_document(content, metadata)
        all_vector_payloads.extend(chunks)
        
    logger.info(f"Generated {len(all_vector_payloads)} total chunks from {len(files)} normalized documents.")
    
    # Send all chunks to embedder
    if all_vector_payloads:
        all_payloads = embed_chunks(all_vector_payloads)
        
        # Save Payload
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_payloads, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Phase 3 Complete. Generated {len(all_payloads)} total chunks with embeddings.")
        return {"chunk_count": len(all_payloads)}
    else:
        logger.info("No chunks were generated.")

if __name__ == "__main__":
    logger.info("Starting Phase 3 Chunking & Embedding Job with Local Inference...")
    run_chunking_and_embedding()
