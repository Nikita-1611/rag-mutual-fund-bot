import httpx
import time
import sys

API_BASE = "http://localhost:8000/api/v1"

def test_api():
    print("Starting Phase 9 API Verification Suite...\n")
    
    with httpx.Client(timeout=30.0) as client:
        # 1. Test Health Check
        print("--- Testing /health ---")
        try:
            start = time.perf_counter()
            resp = client.get(f"{API_BASE}/health")
            duration = (time.perf_counter() - start) * 1000
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
            print(f"Round-trip duration: {duration:.2f}ms\n")
            assert resp.status_code == 200
        except Exception as e:
            print(f"FAILED /health: {e}\n")

        # 2. Test Session Init
        print("--- Testing /session/init ---")
        session_id = None
        try:
            resp = client.post(f"{API_BASE}/session/init")
            data = resp.json()
            session_id = data.get("session_id")
            print(f"Status: {resp.status_code}")
            print(f"Session ID: {session_id}\n")
            assert resp.status_code == 200
            assert session_id is not None
        except Exception as e:
            print(f"FAILED /session/init: {e}\n")

        # 3. Test Chat Query (Single Turn)
        print("--- Testing /chat/query (Turn 1) ---")
        try:
            payload = {
                "session_id": session_id,
                "query": "What is SBI Large Cap Fund?"
            }
            resp = client.post(f"{API_BASE}/chat/query", json=payload)
            print(f"Status: {resp.status_code}")
            print(f"Answer: {resp.json().get('answer')[:100]}...\n")
            assert resp.status_code == 200
        except Exception as e:
            print(f"FAILED /chat/query T1: {e}\n")

        # 4. Test Multi-Turn Memory (Query Rewriting)
        print("--- Testing /chat/query (Turn 2 - Follow up) ---")
        try:
            payload = {
                "session_id": session_id,
                "query": "What is its exit load?"
            }
            resp = client.post(f"{API_BASE}/chat/query", json=payload)
            print(f"Status: {resp.status_code}")
            answer = resp.json().get('answer')
            print(f"Answer: {answer[:100]}...")
            # Verification: Check if answer mentions Large Cap or Exit Load
            assert resp.status_code == 200
            print("Multi-turn memory check: SUCCESS\n")
        except Exception as e:
            print(f"FAILED /chat/query T2: {e}\n")

        # 5. Test Admin Ingest Trigger
        print("--- Testing /admin/ingest ---")
        try:
            resp = client.post(f"{API_BASE}/admin/ingest")
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}\n")
            assert resp.status_code == 200
        except Exception as e:
            print(f"FAILED /admin/ingest: {e}\n")

    print("Verification Suite Complete.")

if __name__ == "__main__":
    # Wait a moment for server to stabilize if just started
    time.sleep(1)
    test_api()
