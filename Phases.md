# Phases.md — Build Roadmap & Team Execution Chain

Each phase ends in something runnable and verified. Do not start a phase until its prerequisites are functionally complete.

---

## 🔗 Team Role Division & 3-Branch Strategy

### 🌿 Branch 1: `main` (Handled by Team Lead / You)
- **Whole Backend:** FastAPI app, Pydantic schemas (`backend/schemas.py`), repo ingestion service (`git clone` & ZIP extraction), async task manager, REST API endpoints.
- **Model Pipeline:** `microsoft/codebert-base` vulnerability classification pipeline on CodeXGLUE Devign dataset.
- **Vector RAG Engine:** Local FAISS vector index + `sentence-transformers` (`all-MiniLM-L6-v2`) on CWE/OWASP corpus.
- **Agent Orchestrator:** LangGraph StateGraph DAG agent (`Ingest` → `Scan` → `RAG` → `Synthesize` → `Report`).
- **Baseline Frontend:** Simple working frontend/test client to test and verify the entire backend and AI pipeline immediately.

### 🌿 Branch 2: `feature/ast-graph-parser` (Handled by Friend 2)
- **AST Slicer:** Function extraction with exact line numbers (`filename.py:L42-L58`) using Python `ast` and `tree-sitter`.
- **Call-Graph Builder:** NetworkX directed dependency graph exporting `{ nodes: [...], edges: [...] }` JSON matching backend schemas.
- **Unit Tests:** `pytest` test suite in `tests/test_parser.py`.

### 🌿 Branch 3: `feature/frontend-dashboard` (Handled Collaboratively by Friends 3 & 4)
- **Modern Dashboard:** React (Vite) + Tailwind CSS dark-mode dashboard (`#0D1117`).
- **Visual Components:** Security Health Score dial (0–100), filterable findings table, side-by-side code diff viewer.
- **Graph Visualizer:** Interactive React Flow call-graph component rendering the backend-provided dependency graph.
- **Polished UX:** Real-time audit progress bar, error handling, and citation modals.

---

## 🔗 Team Execution Chain & Dependency Flow

```
[ STEP 1: Team Lead (main branch) ] ──► Builds Whole Backend & Pydantic Schemas (backend/schemas.py)
                                                     │
      ┌──────────────────────────────────────────────┴──────────────────────────────────────────────┐
      ▼                                                                                             ▼
[ STEP 2: Friend 2 (feature/ast-graph-parser) ]                 [ STEP 2: Friends 3 & 4 (feature/frontend-dashboard) ]
  Builds AST Function Slicer & NetworkX Graph                     Collaboratively build rich React UI & React Flow graph
      │                                                                                             │
      └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                     ▼
                                  [ STEP 3: Push Feature Branches to GitHub ]
                                                     │
                                                     ▼
                                  [ STEP 4: Team Lead Merges PRs into main ]
                                                     │
                                                     ▼
                                  [ STEP 5: End-to-End System Testing & Demo ]
```

---

## 📍 Phase 0 — Backend Foundation & Data Schemas (STEP 1 - Team Lead)
- **Team Lead (You):** 
  - Create directory structure (`backend/`, `ml_pipeline/`, `rag_engine/`, `agent/`).
  - Implement `backend/schemas.py` with Pydantic Data Models (`AuditRequest`, `AuditResult`, `Finding`, `GraphNode`, `GraphEdge`).
  - Create `backend/main.py` with CORS enabled and basic `/api/health` + mock `/api/audit` endpoints.
  - Implement repository ingestor (`backend/services/ingestor.py`) for GitHub shallow cloning and ZIP extraction.
- **Outcome:** Running FastAPI server with interactive Swagger UI at `http://localhost:8000/docs`.

---

## 📍 Phase 1 — AST Code Parser & NetworkX Call Graph (STEP 2 - Friend 2)
- **Friend 2:**
  - Pull `main` branch to get `backend/schemas.py` data contracts.
  - Switch to branch: `git checkout -b feature/ast-graph-parser`.
  - Implement `parser_engine/ast_slicer.py` (extract functions with `L42-L58` line boundaries).
  - Implement `parser_engine/graph_builder.py` (NetworkX graph outputting `{ nodes: [...], edges: [...] }` JSON matching backend schema).
  - Test via `pytest tests/test_parser.py`.
- **Outcome:** Verified parser engine ready for PR merge into `main`.

---

## 📍 Phase 2 & 3 — ML Classifier & Local Vector RAG (STEP 2 - Team Lead)
- **Team Lead (You):**
  - Download/prepare CodeXGLUE Devign vulnerability dataset in `ml_pipeline/`.
  - Implement CodeBERT (`microsoft/codebert-base`) inference & fine-tuning pipeline.
  - Build local FAISS vector DB indexing CWE Top 25 and OWASP security standards with `all-MiniLM-L6-v2`.
- **Outcome:** High-speed, local ML vulnerability scoring and grounded RAG document retrieval.

---

## 📍 Phase 4 & 5 — LangGraph Agent Orchestrator & Backend Wiring (STEP 2 - Team Lead)
- **Team Lead (You):**
  - Build LangGraph StateGraph DAG agent (`Ingest` → `Scan` → `RAG` → `Synthesize` → `Report`).
  - Wire AST parser, CodeBERT model, FAISS RAG, and LangGraph agent into FastAPI endpoints.
  - Build simple baseline frontend to verify end-to-end functionality right away.
- **Outcome:** Fully functional autonomous code review API pipeline running on `main`.

---

## 📍 Phase 6 — Full-Fledged React Dashboard & React Flow (STEP 2 - Friends 3 & 4)
- **Friends 3 & 4 (Collaborative):**
  - Pull `main` branch to get backend schemas and API contracts.
  - Switch to branch: `git checkout -b feature/frontend-dashboard`.
  - Build modern dark-theme React + Vite + Tailwind CSS dashboard (`#0D1117`).
  - Implement Security Health Score dial, filterable findings table, side-by-side code diff viewer, and React Flow interactive call graph.
  - Test locally via `npm run dev` connecting to the FastAPI backend.
- **Outcome:** Production-grade, beautiful frontend ready for PR merge into `main`.

---

## 📍 Phase 7 — Integration, PR Merge & Final Demo (STEPS 3, 4 & 5)
- **Friend 2 and Friends 3 & 4:**
  - Verify code passes tests, ensure build artifacts are in `.gitignore`, update `Memory.md`, and push feature branches.
- **Team Lead:**
  - Review and merge `feature/ast-graph-parser` and `feature/frontend-dashboard` into `main`.
  - Conduct full end-to-end demo test with real GitHub repositories.
- **Full Team:** Prepare presentation slides and live demonstration.
