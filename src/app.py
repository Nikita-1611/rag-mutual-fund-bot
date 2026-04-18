import streamlit as st
import uuid
import sys
import os
import httpx
from datetime import datetime

# API Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")

# Page Configuration
st.set_page_config(
    page_title="Mutual Fund FAQ Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Premium Fintech Look)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* Global Styles */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    .header-logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    .sbi-logo {
        background-color: #1a3d6d;
        color: white;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .main-header {
        font-size: 2.25rem;
        font-weight: 700;
        color: #1a3d6d;
        margin: 0;
        letter-spacing: -0.025em;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    
    /* Disclaimer Box */
    .disclaimer-box {
        background: rgba(254, 226, 226, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid #fecaca;
        padding: 0.75rem 1.25rem;
        border-radius: 0.75rem;
        color: #991b1b;
        font-size: 0.875rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Chat Bubble Enhancements */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .stChatMessage {
        background-color: transparent !important;
        padding: 0 !important;
    }
    
    .message-container {
        padding: 1.25rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        line-height: 1.6;
    }
    
    .user-message {
        background-color: #ffffff;
        border-left: 4px solid #3b82f6;
        color: #1e293b;
    }
    
    .bot-message {
        background-color: #f1f5f9;
        border-left: 4px solid #10b981;
        color: #0f172a;
    }
    
    /* Source Card */
    .source-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
        margin-top: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        font-size: 0.8125rem;
    }
    .source-label {
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.7rem;
    }
    .source-link {
        color: #2563eb;
        text-decoration: none;
        font-weight: 500;
        word-break: break-all;
    }
    .source-link:hover {
        text-decoration: underline;
    }
    .update-date {
        color: #94a3b8;
        font-style: italic;
    }
    
    /* Sidebar Status */
    .sidebar-status {
        padding: 0.5rem 0.75rem;
        background: #ecfdf5;
        border-radius: 0.5rem;
        color: #065f46;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 1rem;
    }
    .status-dot {
        height: 8px;
        width: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Helper for API calls
def call_api(method: str, endpoint: str, data: dict = None):
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = httpx.get(url, timeout=30.0)
        else:
            response = httpx.post(url, json=data, timeout=60.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Backend API Unreachable: {e}")
        return None

# Check Backend Health
health = call_api("GET", "/health")
is_live = health and health.get("status") == "healthy"

# Initialize Session State
if "threads" not in st.session_state:
    st.session_state.threads = {}
if "current_thread_id" not in st.session_state:
    resp = call_api("POST", "/session/init")
    if resp:
        tid = resp["session_id"]
        st.session_state.threads[tid] = []
        st.session_state.current_thread_id = tid

# Sidebar: Thread Management & Branding
with st.sidebar:
    st.markdown(f"""
        <div class="sidebar-status">
            <span class="status-dot"></span> {"SECURE & LIVE" if is_live else "SERVICES DEGRADED"}
        </div>
    """, unsafe_allow_html=True)
    
    st.title("📈 MF Assistant")
    st.caption("Factual Mutual Fund Data")
    
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        resp = call_api("POST", "/session/init")
        if resp:
            new_id = resp["session_id"]
            st.session_state.threads[new_id] = []
            st.session_state.current_thread_id = new_id
            st.rerun()

    st.divider()
    st.subheader("Chat History")
    for tid in reversed(list(st.session_state.threads.keys())):
        history = st.session_state.threads[tid]
        label = "📝 " + (history[0]["content"][:24] + "..." if history else f"New Chat")
        is_active = tid == st.session_state.current_thread_id
        if st.button(label, key=f"btn_{tid}", use_container_width=True, 
                     type="secondary" if not is_active else "primary"):
            st.session_state.current_thread_id = tid
            st.rerun()

    st.write("")
    st.subheader("Fund Catalog")
    st.markdown("""
    <ul style="font-size: 0.85rem; color: #64748b;">
        <li>SBI ELSS Tax Saver</li>
        <li>SBI Flexicap</li>
        <li>SBI Large Cap</li>
        <li>SBI Magnum Multiplier</li>
        <li>SBI Small Midcap</li>
    </ul>
    """, unsafe_allow_html=True)
    st.write("")

    if st.button("🗑️ Clear Current Thread", use_container_width=True):
        st.session_state.threads[st.session_state.current_thread_id] = []
        st.rerun()

# Main UI Header
st.markdown("""
<div class="header-logo-container">
    <h1 class="main-header">SBI Mutual Fund FAQ Assistant</h1>
</div>
""", unsafe_allow_html=True)
st.markdown('<p class="sub-header">Official factual guidance for SBI Mutual Fund investment queries.</p>', unsafe_allow_html=True)
st.markdown('<div class="disclaimer-box">⚠️ Facts-only. No investment advice.</div>', unsafe_allow_html=True)

# Helper to render bot response with source card
def render_bot_response(payload):
    if not payload:
        st.error("Empty response received from the engine.")
        return
        
    answer = payload.get("answer", "No answer provided.")
    st.markdown(f'<div class="message-container bot-message">{answer}</div>', unsafe_allow_html=True)
    
    source_url = payload.get("source_url", "N/A")
    if source_url not in ["N/A", ""]:
        st.markdown(f"""
            <div class="source-card">
                <div class="source-label">OFFICIAL SOURCE</div>
                <a href="{source_url}" target="_blank" class="source-link">🔗 {source_url}</a>
                <div class="update-date">Verified on {payload.get('last_updated', 'N/A')}</div>
            </div>
        """, unsafe_allow_html=True)

# Main Chat Rendering Loop
curr_id = st.session_state.current_thread_id
history = st.session_state.threads.get(curr_id, [])

for msg in history:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f'<div class="message-container user-message">{msg.get("content", "")}</div>', unsafe_allow_html=True)
        else:
            payload = msg.get("payload") or {"answer": msg["content"]}
            render_bot_response(payload)

# Handle new user input
if user_input := st.chat_input("Ask about any SBI mutual fund..."):
    st.session_state.threads[curr_id].append({"role": "user", "content": user_input})
    st.rerun()

# Process user input if exists
if history and history[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Retrieving official documentation..."):
            resp = call_api("POST", "/chat/query", data={
                "session_id": curr_id,
                "query": history[-1]["content"]
            })
            if resp:
                render_bot_response(resp)
                st.session_state.threads[curr_id].append({
                    "role": "assistant", 
                    "payload": resp,
                    "content": resp["answer"]
                })
                st.rerun()

# Onboarding suggested questions if empty
if not history:
    st.divider()
    st.markdown("### 👋 How can I assist you today?")
    st.write("Try one of these factual questions:")
    cols = st.columns(3)
    examples = [
        "What is the lock-in period for SBI ELSS Tax Saver?",
        "What is the exit load for SBI Flexicap?",
        "What is the minimum SIP for SBI Large Cap?"
    ]
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.threads[curr_id].append({"role": "user", "content": ex})
            st.rerun()
