import os
import sys
import logging

# Set up path so we can import our modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from pipeline.phase5_retrieval.retriever import RAGRetriever

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def debug_flow():
    retriever = RAGRetriever()
    
    # 1. First Turn
    print("\n--- TURN 1 ---")
    q1 = "What is SBI Large Cap Fund?"
    history = []
    print(f"User: {q1}")
    res1 = retriever.query(q1, history=history)
    print(f"Assistant: {res1.get('answer')[:100]}...")
    
    # Update history manually as app.py does
    history.append({"role": "user", "content": q1})
    history.append({"role": "assistant", "content": res1.get("answer")})
    
    # 2. Second Turn (The problematic one)
    print("\n--- TURN 2 ---")
    q2 = "What is its NAV?"
    print(f"User: {q2}")
    
    # We will manually call _rewrite_query to see the internal output
    rewritten = retriever._rewrite_query(q2, history)
    print(f"DEBUG: Rewritten Query -> '{rewritten}'")
    
    res2 = retriever.query(q2, history=history)
    print(f"Assistant: {res2.get('answer')}")
    print(f"Source URL: {res2.get('source_url')}")
    print(f"Is Refusal: {res2.get('is_refusal')}")

if __name__ == "__main__":
    debug_flow()
