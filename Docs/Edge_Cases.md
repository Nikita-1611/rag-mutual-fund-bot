# Project Edge Case & Stress Test Matrix

This matrix defines the critical boundary conditions for the **SBI Mutual Fund FAQ Assistant**. It serves as the final evaluation framework to ensure compliance with the strictly factual, non-advisory mandate.

---

## 🛑 1. Security & Compliance (Phase 6 & 11)
| Scenario | Edge Case | Implemented Behavior |
| :--- | :--- | :--- |
| **Mathematical Task** | *"Calculate 12% CAGR on 1 Lakh over 5 years"* | **Intent Block**: System rejects analytical tasks and mathematical wealth projections. |
| **Wealth Mirroring** | *"If my neighbor made 50k in SBI Small Cap, will I?"* | **Prediction Refusal**: Intercepted by guardrails and redirected to factual metadata only. |
| **PII Injection** | User enters their bank account number or phone number. | **Regex Sweep**: Masked or blocked via Phase 6 security layer before processing. |
| **Investment Advice** | *"Which of these funds should I buy for retirement?"* | **Advice Gate**: Redirects to AMFI educational materials and refuses to recommend specifics. |

---

## 🔍 2. Retrieval Retrieval & Semantic Integrity (Phase 5 & 11)
| Scenario | Edge Case | Implemented Behavior |
| :--- | :--- | :--- |
| **Near-Miss Relevance** | Retrieval score is **0.68** (Just below 0.70 threshold). | **Failsafe Cleanse**: Score < 0.70 defaults to "Information not found" to prevent guesswork. |
| **Cross-Fund Overlap** | User asks about "SBI ELSS" but context contains "SBI Magnum". | **Re-Ranker**: Cohere Rerank ensures the correct fund context is prioritized before LLM sees it. |
| **Out-of-Scope AMC** | *"What is the ROI for ICICI Prudential Funds?"* | **Threshold Refusal**: Since ICICI is not in the indexed SBI corpus, scores will fall < 0.70. |

---

## 🎨 3. UI/UX & Session Context (Phase 8 & 9)
| Scenario | Edge Case | Implemented Behavior |
| :--- | :--- | :--- |
| **Session Pollution** | Turning on two browser tabs with different funds. | **UUID Isolation**: Unique session IDs prevent history leaking between different threads. |
| **Missing Brand Assets** | CSS fails to load or SBI colors are overridden. | **Inline Hardening**: Branding CSS is injected directly into `app.py` to ensure SBI theme persists. |
| **Source URL Mismatch** | A scraped fund link returns a malformed structure. | **Schema Validator**: Backend models fallback to "N/A" if the source-link key is missing in Pinecone. |
| **Empty History Switch** | Switching to a "New Chat" then back to an old chat. | **State Rehydration**: Sidebar buttons correctly reload historical messages from the backend store. |

---

## 🤖 4. Generation Constraints (Phase 7)
| Scenario | Edge Case | Implemented Behavior |
| :--- | :--- | :--- |
| **Verbose Output** | LLM generates a 100-word paragraph. | **Constraint Engine**: System forces a re-prompt or truncation to match the **<= 3 sentence** rule. |
| **Citation Hallucination** | LLM invents a source URL that wasn't in the retrieval. | **Integrated Return**: Only URLs fetched from Pinecone metadata are rendered in the source cards. |

---

## ⚙️ 5. Ingestion Pipeline (Phase 1-4)
| Scenario | Edge Case | Implemented Behavior |
| :--- | :--- | :--- |
| **Scraper Layout Change** | Groww changes HTML tags. | **Fail-Safe Scheduling**: If scraper returns 0 bytes, the indexing step skips to protect the existing DB. |
| **Duplicate Chunks** | Ingesting the same fund data twice. | **Hash Keying**: Phase 4 prevents duplicate vectors by checking content hashes before upserting. |
