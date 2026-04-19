# 📈 SBI Mutual Fund FAQ Assistant (RAG)

A production-ready Retrieval-Augmented Generation (RAG) system for strict, facts-only mutual fund queries.

## 🚀 Overview
This assistant is engineered for **factual accuracy and compliance**. It retrieves information exclusively from official AMC (Asset Management Company) documentation and enforces strict output constraints (<= 3 sentences, mandatory source links).

### Core Features
- **Semantic Retrieval**: Powered by `bge-small-en-v1.5` embeddings and Pinecone.
- **Multi-Turn Memory**: Maintains conversation context via high-accuracy query rewriting.
- **Compliance Guardrails**: Automatically detects and refuses investment advice or PII using zero-shot classification.
- **Premium UI**: Minimalist, fintech-inspired Streamlit interface with isolated chat threads.

---

## 🛠️ Technology Stack
- **Frontend**: Streamlit
- **Backend API**: FastAPI
- **LLM Engine**: Llama-3.1 (via Groq)
- **Re-Ranker**: Cohere Rerank-v3
- **Vector DB**: Pinecone
- **Observability**: LangSmith
- **Evaluation**: Ragas

---

## 📦 Installation & Setup

### 1. Prerequisites
- Python 3.11+
- API Keys for: **Groq**, **Cohere**, and **Pinecone**.

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY="your_key"
COHERE_API_KEY="your_key"
PINECONE_API_KEY="your_key"

# Optional: LangSmith Tracing
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your_key"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

---

## ⚡ Execution

### Full Ingestion Pipeline
To scrape Groww data and update the knowledge base:
```bash
python run_tests.py
```

### Start Backend API
```bash
python src/api/main.py
```

### Start Streamlit UI
```bash
streamlit run src/app.py
```

---

## 📊 Phase 10: Evaluation
Run the Ragas evaluation suite to measure faithfulness and relevancy:
```bash
python src/pipeline/phase10_evaluation/evaluate.py
```

---

## 🛡️ Compliance & Safety
- **Anti-Advice**: Zero-Shot classification intercepts subjective queries.
- **PII Scrubbing**: Regex-based pre-flight sweeps for PAN, Aadhaar, and contacts.
- **Factual Gate**: LLM temperature `0.0` + context-only prompting.

---
*Created as part of the Mutual Fund FAQ Assistant RAG Project.*
