# Deployment Plan - Mutual Fund FAQ Assistant

This document outlines the final production deployment strategy for the **SBI Mutual Fund FAQ Assistant**. All 11 architectural phases have been implemented and verified.

## 🏁 Phase Implementation Status

| Phase | Description | Status | Verification |
| :--- | :--- | :--- | :--- |
| **P1-4** | Data Ingestion Pipeline (Scraper, Normalize, Chunk, Index) | **READY** | GitHub Actions Scheduler |
| **P5-7** | RAG retrieval, Semantic Rewriter, and Generation Engine | **READY** | Cohere Re-rank + Llama-3 |
| **P8** | **Next.js 15+ Premium Dashboard** | **READY** | SBI Navy/White UI on Vercel |
| **P9-10** | FastAPI Backend Integration & Session Management | **READY** | `/api/v1` Service Layer on Render |
| **P11** | Mitigation Engine (Thresholds & Math Guardrails) | **READY** | 0.70 Similarity + Intent Block |

---

## 🏗️ Cloud Infrastructure (Production)

| Component | Platform | Primary Role |
| :--- | :--- | :--- |
| **Frontend UI** | [Vercel](https://vercel.com) | Hosts the **Next.js** high-performance dashboard. |
| **Backend API** | [Render](https://render.com) | Executes the **FastAPI** RAG engine and manages session histories. |
| **Scheduler** | [GitHub Actions](https://github.com/features/actions) | Orchestrates daily **Ingestion** (Scraping -> Indexing) via Cron. |
| **Vector DB** | [Pinecone (Serverless)](https://pinecone.io) | High-performance semantic retrieval storage. |

### 🔑 Required Secrets
- `PINECONE_API_KEY`: Vector storage access (Render, GitHub Actions).
- `GROQ_API_KEY`: Llama-3 inference (Render).
- `COHERE_API_KEY`: Cross-Encoder re-ranking (Render).
- `NEXT_PUBLIC_API_URL`: Points to Render Backend (Vercel).

---

## 🚦 Security & Hallucination Guardrails

The production deployment incorporates two critical Phase 11 safety layers:

### 1. Similarity Gate (Hallucination Prevention)
- **Mechanism**: Cosine Similarity Scoring.
- **Enforcement**: Any retrieval result with a confidence score **< 0.70** is automatically discarded.
- **Fallback**: The user receives a "Factual information not found" refusal to prevent guessing.

### 2. Analytical Intent Guardrail
- **Mechanism**: Prompt-based Intent Classification in `guardrails.py`.
- **Enforcement**: Mathematical calculations, wealth projections, and "What-if" scenarios are explicitly blocked.
- **Disclaimer**: The system remains strictly factual and redirects users to unofficial calculators for math tasks.

---

## 🛠️ Launch Commands

### 1. Backend Service (Render)
```powershell
# Build Command
pip install -r requirements.txt
# Start Command
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

### 2. Frontend Dashboard (Vercel)
- **Framework**: Next.js (App Router)
- **Directory**: `frontend/`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Environment Variable**: `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api/v1`

### 3. Scheduler (GitHub Actions)
- **Manual Trigger**: `python src/scheduler_local.py`
- **Automation**: Managed via `.github/workflows/ingestion.yml` triggering the 4 ingestion phases daily.

### 4. Verification
Access `https://your-backend.onrender.com/api/v1/health` to confirm the triple-connectivity (Pinecone + Groq + Cohere) before opening the frontend.
