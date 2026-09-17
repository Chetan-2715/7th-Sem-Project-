# Phases.md — Build Roadmap & Team Execution Chain

Each phase ends in something runnable and verified. Do not start a phase until its prerequisites are functionally complete.

---

## 🔗 Team Execution Chain & Dependency Flow

```
[ STEP 1: Friend 3 (Backend) ] ──► Pydantic Schemas (backend/schemas.py)
                                           │
      ┌────────────────────────────────────┼────────────────────────────────────┐
      ▼                                    ▼                                    ▼
[ STEP 2: Friend 2 (AST Parser) ]  [ STEP 2: Friend 3 (Backend Logic) ]  [ STEP 2: Friend 4 (Frontend UI) ]
  Slices AST & NetworkX Graph        Repo Ingestion & REST API             React Dashboard & React Flow
      │                                    │                                    │
      └────────────────────────────────────┼────────────────────────────────────┘
                                           ▼
                      [ STEP 3: Push Feature Branches to GitHub ]
                                           │
                                           ▼
                      [ STEP 4: Team Lead Merges PRs into main ]
                                           │
                                           ▼
                      [ STEP 5: End-to-End System Testing ]
```

---

## 📍 Phase 0 — Setup & Data Contracts (PREREQUISITE - STEP 1)
- **Friend 3 (Backend Lead):** Create `backend/schemas.py` with Pydantic Data Models (`AuditRequest`, `AuditResult`, `Finding`, `GraphNode`, `GraphEdge`) and setup FastAPI dummy endpoint.
- **Friend 4 (Frontend Lead):** Initialize React Vite project in `frontend/` and connect UI to Friend 3's mock schemas.
- **Friend 2 (AST Lead):** Initialize `parser_engine/` module.
- **Team Lead (AI):** Setup `ml_pipeline/` and `rag_engine/` module directories.

---

## 📍 Phase 1 — Repo Ingestion & AST Call Graph (STEP 2 - PARALLEL)
- **Friend 3 (Backend Lead):** Implement `backend/services/ingestor.py` (`git clone --depth 1` and ZIP extractor).
- **Friend 2 (AST Lead):** Implement `parser_engine/ast_slicer.py` (extract functions `filename.py:L42-L58`) & `graph_builder.py` (NetworkX graph outputting `{ nodes: [...], edges: [...] }` JSON matching Friend 3's schema).
- **Verification:** Friend 2 tests `parser_engine/tests/` via `pytest`; Friend 3 tests ingestion via Swagger `/docs`.

---

## 📍 Phase 2 & 3 — Trained Classifier & Vector RAG Pipeline (STEP 2 - PARALLEL)
- **Team Lead (AI):** 
  - Fine-tune CodeBERT model on CodeXGLUE Devign dataset.
  - Build local FAISS vector indexer over CWE/OWASP documentation.
- **Verification:** Evaluate accuracy metrics and sub-millisecond retrieval.

---

## 📍 Phase 4 & 5 — Agent Orchestration & Backend REST API (STEP 2/3)
- **Team Lead (AI):** Construct LangGraph StateGraph agent (`Ingest` → `Scan` → `RAG` → `Synthesize` → `Report`).
- **Friend 3 (Backend Lead):** Complete FastAPI REST routes (`/api/health`, `/api/audit`, `/api/status`, `/api/report`).
- **Verification:** All API responses validated for syntax, edge cases, and zero runtime errors.

---

## 📍 Phase 6 — Frontend Dashboard & Graph UI (STEP 2/3)
- **Friend 4 (Frontend Lead):** Build dark-mode dashboard layout (`#0D1117`), Security Health Score dial (0–100), filterable findings table, side-by-side code diff viewer, and `reactflow` graph visualizer.
- **Verification:** Run `npm run dev` to confirm clean, responsive rendering without console errors.

---

## 📍 Phase 7 — PR Merge, Integration & Final Demo (STEPS 4 & 5)
- **Team Members 2, 3, 4:** Verify code passes all tests, update `Memory.md`, add all unwanted files (`__pycache__`, `.venv`, `node_modules/`) to `.gitignore`, and push feature branches.
- **Team Lead:** Review and merge PRs into `main`, connect AI pipeline into FastAPI backend, and perform end-to-end testing with real GitHub repos.

---

## Explicitly Deferred (Post-v1 Stretch Goals)
- Multi-language parser expansion (beyond Python/C/C++/JS)
- CI/CD automated PR scanner
- Auto-commit refactored code to remote repositories
