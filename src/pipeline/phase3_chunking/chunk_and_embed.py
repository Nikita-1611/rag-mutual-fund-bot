import os
import json
import uuid
import logging
import re
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
import cohere

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) # RAG directory
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))
INPUT_DIR = os.path.join(ROOT_DIR, "output", "normalized")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "embedded")

def check_tabular(chunk_text: str) -> bool:
    """Checks if the markdown text chunk contains a table format."""
    return "|---" in chunk_text or "| ---" in chunk_text

def strip_groww_noise(text: str) -> str:
    """Removes standard Groww website navigation headers and footers."""
    # Find the start of the actual content
    # Standard Groww fund pages have "3Y annualised" or "1Y annualised" or "NAV:" near the top
    start_markers = ["3Y annualised", "NAV:", "Fund size (AUM)"]
    start_index = 0
    
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            # Back up a bit to include any nearby headers, or just start at marker
            start_index = max(0, idx - 100)
            break
            
    # Find the start of the footer noise
    end_markers = ["Download the App", "© 2016-2026 Groww", "Vaishnavi Tech Park"]
    end_index = len(text)
    
    for marker in end_markers:
        idx = text.find(marker, start_index)
        if idx != -1:
            end_index = idx
            break
            
    return text[start_index:end_index].strip()

def chunk_document(content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Splits document and infuses chunk-level metadata."""
    # Split by character count to avoid tiktoken binary dependency on Render
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, # Approx 500 tokens
        chunk_overlap=150,
        separators=["\n\n", "\n", " "]
    )
    
    # 1. Clean the content of the frontmatter if it's causing noise
    # (Optional, but let's keep the focus on prepending the verified tags)
    clean_content = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            clean_content = parts[2].strip()
            
    # NEW: Strip Groww-specific navigation/footer noise
    clean_content = strip_groww_noise(clean_content)
            
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
    """Embeds a batch of chunks using Cohere's embed-english-light-v3.0 (384-dim)."""
    co_api = os.environ.get("COHERE_API_KEY")
    if not co_api:
        logger.error("COHERE_API_KEY not found in environment!")
        raise ValueError("COHERE_API_KEY missing.")
        
    co = cohere.Client(co_api)
    
    BATCH_SIZE = 96 # Cohere v3 supports up to 96 texts per batch
    total_chunks = len(chunks)
    
    logger.info(f"Starting Cohere embedding for {total_chunks} chunks...")
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        
        logger.info(f"Submitting batch {i} to {min(i+BATCH_SIZE, total_chunks)} to Cohere...")
        
        try:
            response = co.embed(
                texts=texts,
                model='embed-english-light-v3.0',
                input_type='search_document',
                embedding_types=['float']
            )
            # Cohere v3 returns 'float' embeddings in 'embeddings.float'
            # (or just 'embeddings' depending on the response object)
            embeddings = response.embeddings.float
            
            # Map embeddings back to chunks
            for j, embedding in enumerate(embeddings):
                batch[j]["embedding"] = embedding
                
        except Exception as e:
            logger.error(f"Cohere embedding failed: {e}")
            raise
            
    logger.info(f"Successfully vectorized {total_chunks} chunks via Cohere.")
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
        output_file = os.path.join(OUTPUT_DIR, "vector_payloads.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_payloads, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Phase 3 Complete. Generated {len(all_payloads)} total chunks with embeddings.")
        return {"chunk_count": len(all_payloads)}
    else:
        logger.info("No chunks were generated.")

if __name__ == "__main__":
    logger.info("Starting Phase 3 Chunking & Embedding Job with Local Inference...")
    run_chunking_and_embedding()
