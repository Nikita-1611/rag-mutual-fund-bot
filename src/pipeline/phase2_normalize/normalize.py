import os
import json
import hashlib
from datetime import datetime, timezone
import logging
import re

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # RAG directory
INPUT_DIR = os.path.join(ROOT_DIR, "..", "output", "raw_markdown")
OUTPUT_DIR = os.path.join(ROOT_DIR, "..", "output", "normalized")
HASHES_FILE = os.path.join(ROOT_DIR, "..", "output", "hashes.json")

def load_hashes() -> dict:
    if os.path.exists(HASHES_FILE):
        with open(HASHES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_hashes(hashes_dict: dict):
    with open(HASHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(hashes_dict, f, indent=4)

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_metadata(content: str, filename: str) -> dict:
    metadata = {
        "source_url": "",
        "scheme_name": "",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    # Extract source_url from YAML frontmatter
    url_match = re.search(r'source_url:\s*(https?://[^\s]+)', content)
    if url_match:
        metadata["source_url"] = url_match.group(1)
        
    # Extract scheme_name from logic (e.g. filename or first title)
    # Since we know they are Groww urls, we can try to find the mutual fund name.
    # Usually it's in the text or we can format the filename slug.
    slug = filename.replace('.md', '')
    formatted_name = " ".join(word.capitalize() for word in slug.split('-'))
    metadata["scheme_name"] = formatted_name
    
    return metadata

def run_normalizer():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    hashes = load_hashes()
    updated_hashes = hashes.copy()
    
    if not os.path.exists(INPUT_DIR):
        logger.warning(f"Input directory not found: {INPUT_DIR}. Please run Phase 1 Scraping first.")
        return

    processed_count = 0
    skipped_count = 0

    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith('.md'):
            continue
            
        file_path = os.path.join(INPUT_DIR, filename)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content_hash = compute_hash(content)
        
        # Deduplication check
        if filename in hashes and hashes[filename] == content_hash:
            logger.info(f"Skipping {filename}: Hash unchanged.")
            skipped_count += 1
            continue
            
        # Normalization and Tagging
        metadata = extract_metadata(content, filename)
        
        normalized_data = {
            "metadata": metadata,
            "hash": content_hash,
            "content": content
        }
        
        output_filename = filename.replace('.md', '.json')
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(normalized_data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Processed and normalized: {filename}")
        updated_hashes[filename] = content_hash
        processed_count += 1
        
    save_hashes(updated_hashes)
    logger.info(f"Phase 2 Complete. Processed: {processed_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    logger.info("Starting Phase 2 Normalization Job...")
    run_normalizer()
