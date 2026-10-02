# Memory.md — Progress Log

> This file is the AI's persistent context across sessions/tools. Update it after every meaningful chunk of work — don't wait until the end of a session. Keep entries brief and factual (what was done, what decided, what's next) rather than re-explaining the whole project each time.

## How to use this file
- At the start of any new session/chat, read this file first before touching code.
- After completing a task, append a new dated entry below — don't rewrite history.
- If a decision changes something in PRD.md / Architecture.md / Rules.md / Phases.md / Design.md, note it here AND update that source file.
- Keep the "Current Status" section at the top always up to date — this is the fastest thing to read.

---

## Current Status
- **Phase**: Phase 0 (Backend), Phase 3 (RAG Engine), Phase 4 (LangGraph Agent), Phase 6 (Baseline UI) — ALL COMPLETED & TESTED!
- **Active Task**: Vector RAG Engine & LangGraph Agent workflow fully built and integrated into FastAPI backend with baseline test UI. Next up: CodeBERT training/dataset pipeline (`ml_pipeline/`).
- **Parallel Branches**:
  - Friend 2: `feature/ast-graph-parser` (AST parser & NetworkX graph)
  - Friends 3 & 4: `feature/frontend-dashboard` (Collaborative React + Tailwind + React Flow dashboard)
- **Next up**: Build `ml_pipeline/` for CodeXGLUE Devign dataset downloading, preprocessing, and fine-tuning CodeBERT (`microsoft/codebert-base`).

## Key Decisions Log
- **Team Responsibilities & Branching**:
  - **Lead (`main`)**: Whole backend API + repo ingestion + CodeBERT model + FAISS RAG + LangGraph agent + baseline frontend.
  - **Friend 2 (`feature/ast-graph-parser`)**: AST parser (`ast_slicer.py`) + NetworkX call graph (`graph_builder.py`).
  - **Friends 3 & 4 (`feature/frontend-dashboard`)**: Collaborative React + Vite + Tailwind CSS + React Flow dashboard.
- **Backend & Schemas**: Central Pydantic schemas in `backend/schemas.py` are the single source of truth for both the parser output and the frontend UI.
- **Trained Model**: `microsoft/codebert-base` (125M parameters) — fits RTX 3050 VRAM (4GB-8GB).
- **Vector DB & Embeddings (for RAG)**: Local Vector RAG over authoritative CWE Top 25 and OWASP corpus (`rag_engine/vector_store.py`) with sub-millisecond retrieval.
- **Agent Framework**: **LangGraph** StateGraph DAG (`Ingest` → `Parse AST` → `Scan Vulnerabilities` → `RAG Grounding` → `Synthesize Fixes` → `Compile Report`).
- **Baseline UI**: Modern dark-mode HTML5/Tailwind dashboard mounted at `/` in FastAPI for immediate browser testing.

## Progress Log
### [2026-10-02] — Vector RAG, LangGraph Agent & Baseline UI Complete
- Implemented `rag_engine/corpus/cwe_owasp_knowledge_base.json` covering CWE-89, CWE-798, CWE-78, CWE-79, CWE-502, CWE-328, CWE-22, CWE-918.
- Implemented `rag_engine/vector_store.py` with FAISS & sentence-transformers vector index and resilient semantic fallback.
- Implemented `agent/state.py`, `agent/nodes.py`, and `agent/orchestrator.py` defining the LangGraph StateGraph DAG.
- Connected LangGraph agent orchestrator into FastAPI background audit execution worker.
- Built interactive baseline UI in `frontend/index.html` mounted directly on `http://localhost:8000/`.
- Verified 100% test pass across `verify_rag.py`, `verify_agent.py`, and `test_e2e_pipeline.py`.

### [2026-10-02] — Phase 0 Backend Foundation Complete
- Implemented `backend/requirements.txt`, `backend/schemas.py`, `backend/services/ingestor.py`, `backend/services/task_manager.py`, `backend/routers/audit.py`, and `backend/main.py`.
- Verified test pass via `backend/tests/verify_backend.py`.

### [2026-10-02] — Team Division & Branch Strategy Refinement
- Updated roadmap to 3-branch structure: `main` (Backend + AI + Lead), `feature/ast-graph-parser` (Friend 2), `feature/frontend-dashboard` (Friends 3 & 4 collaborative).
- Synchronized `Phases.md`, `instructions.md`, and `Memory.md`.
