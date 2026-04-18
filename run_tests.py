import subprocess
import time
import sys

phases = [
    ("Phase 1: Scraping", "src/pipeline/phase1_scraping/scraper.py"),
    ("Phase 2: Normalize", "src/pipeline/phase2_normalize/normalize.py"),
    ("Phase 3: Chunking & Embedding", "src/pipeline/phase3_chunking/chunk_and_embed.py"),
    ("Phase 4: Indexing (Pinecone)", "src/pipeline/phase4_indexing/index_data.py"),
    ("Phase 5: Retrieval & Generation", "src/pipeline/phase5_retrieval/retriever.py"),
]

results = []

def run_phase(name, script_path):
    print(f"\n[{name}] - Starting execution...")
    start_time = time.time()
    try:
        # Run process with src in PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True, env=env)
        duration = time.time() - start_time
        print(f"[{name}] - SUCCESS (Took {duration:.2f}s)")
        # Store last few lines of output
        tail = "\n".join(result.stdout.strip().split("\n")[-3:])
        if not tail:
            tail = "\n".join(result.stderr.strip().split("\n")[-3:])
        results.append((name, "PASS", duration, tail))
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"[{name}] - FAILED (Took {duration:.2f}s)")
        tail = "\n".join(e.stderr.strip().split("\n")[-5:])
        results.append((name, "FAIL", duration, tail))
        return False
    return True

if __name__ == "__main__":
    print("====================================")
    print(" RAG PIPELINE DIAGNOSTIC SUITE ")
    print("====================================")
    
    # Optionally clear hashes to force full re-run
    import os
    if os.path.exists("output/hashes.json"):
        os.remove("output/hashes.json")
        print("Cleared hashes.json to force a fresh pipeline run.")
        
    for name, script in phases:
        success = run_phase(name, script)
        if not success:
            print(f"\nPipeline halted at {name} due to failure.")
            break
            
    print("\n\n====================================")
    print(" DIAGNOSTIC REPORT ")
    print("====================================")
    for name, status, duration, tail in results:
        indicator = "[OK]" if status == "PASS" else "[FAIL]"
        print(f"{indicator} {name} - {status} ({duration:.2f}s)")
        print(f"   Last logs: {tail}")
        print("-" * 40)
