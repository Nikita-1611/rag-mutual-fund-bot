import os
import sys
import logging
from datetime import datetime

# Adjust path to include src
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from pipeline.phase1_scraping.scraper import run_scraper
from pipeline.phase2_normalize.normalize import run_normalizer
from pipeline.phase3_chunking.chunk_and_embed import run_chunking_and_embedding
from pipeline.phase4_indexing.index_data import run_indexing

def setup_logging():
    """Configures logging to both console and file."""
    log_dir = os.path.join(os.path.dirname(PROJECT_ROOT), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'ingestion.log')
    
    # Custom logger for the scheduler
    logger = logging.getLogger('scheduler')
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
    
    # File Handler
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def clear_local_output(logger):
    """Purges the output directory to ensure only fresh data is indexed."""
    base_output = os.path.join(os.path.dirname(PROJECT_ROOT), 'output')
    subdirs = ['raw_markdown', 'normalized', 'embedded']
    
    logger.info(">>> CLEANUP: Purging local stale output files and hashes...")
    
    # 1. Clear directories
    for subdir in subdirs:
        dir_path = os.path.join(base_output, subdir)
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            for f in files:
                try:
                    os.remove(os.path.join(dir_path, f))
                except Exception as e:
                    logger.warning(f"Could not remove {f}: {e}")
    
    # 2. Clear hashes.json to force re-processing
    hashes_path = os.path.join(base_output, 'hashes.json')
    if os.path.exists(hashes_path):
        try:
            os.remove(hashes_path)
            logger.info("CLEANUP: hashes.json removed.")
        except Exception as e:
            logger.warning(f"Could not remove hashes.json: {e}")

    logger.info("CLEANUP COMPLETE: Local cache is fresh.")

def run_pipeline():
    logger = setup_logging()
    
    logger.info("="*50)
    logger.info("LOCAL INGESTION SCHEDULER STARTED")
    logger.info("="*50)

    # NEW: Data Retention Policy (Clear Local Stale Data)
    clear_local_output(logger)
    
    start_time = datetime.now()
    
    try:
        # Phase 1: Scraping
        logger.info(">>> PHASE 1: STARTING WEB SCRAPING...")
        scraper_stats = run_scraper()
        logger.info(f"PHASE 1 COMPLETE: {scraper_stats}")
        
        # Phase 2: Normalization
        logger.info(">>> PHASE 2: STARTING DATA NORMALIZATION...")
        norm_stats = run_normalizer()
        logger.info(f"PHASE 2 COMPLETE: {norm_stats}")
        
        # Phase 3: Chunking & Embedding
        logger.info(">>> PHASE 3: STARTING CHUNKING & EMBEDDING...")
        chunk_stats = run_chunking_and_embedding()
        logger.info(f"PHASE 3 COMPLETE: {chunk_stats}")
        
        # Phase 4: Indexing
        logger.info(">>> PHASE 4: STARTING PINE CONE INDEXING...")
        index_stats = run_indexing()
        logger.info(f"PHASE 4 COMPLETE: {index_stats}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("="*50)
        logger.info(f"INGESTION SUCCESSFUL | Duration: {duration}")
        logger.info("="*50)
        
        # Create summary artifact
        summary_path = os.path.join(os.path.dirname(PROJECT_ROOT), 'logs', 'summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"SBI Mutual Fund Assistant - Ingestion Summary\n")
            f.write(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"--------------------------------------------\n")
            f.write(f"Phase 1 (Scraper):   {scraper_stats}\n")
            f.write(f"Phase 2 (Normalize): {norm_stats}\n")
            f.write(f"Phase 3 (Chunking):  {chunk_stats}\n")
            f.write(f"Phase 4 (Indexing):  {index_stats}\n")
            f.write(f"--------------------------------------------\n")
            f.write(f"RESULT: 100% SUCCESSFUL\n")
            
        logger.info(f"Summary written to {summary_path}")
        
    except Exception as e:
        logger.error(f"FATAL ERROR DURING INGESTION: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
