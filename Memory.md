# Memory.md — Progress Log

> This file is the AI's persistent context across sessions/tools. Update it after every meaningful chunk of work — don't wait until the end of a session. Keep entries brief and factual (what was done, what decided, what's next) rather than re-explaining the whole project each time.

## How to use this file
- At the start of any new session/chat, read this file first before touching code.
- After completing a task, append a new dated entry below — don't rewrite history.
- If a decision changes something in PRD.md / Architecture.md / Rules.md / Phases.md / Design.md, note it here AND update that source file.
- Keep the "Current Status" section at the top always up to date — this is the fastest thing to read.

---

## Current Status
- **Phase**: Phase 0 — Backend Foundation (COMPLETED) | Phase 2 & 3 — RAG & Agent Pipeline (Next)
- **Active Task**: Whole FastAPI Backend built and verified (schemas, ingestor, task manager, audit routes, CORS, unit tests). Ready to build FAISS RAG and LangGraph agent.
- **Parallel Branches**:
  - Friend 2: `feature/ast-graph-parser` (AST parser & NetworkX graph)
  - Friends 3 & 4: `feature/frontend-dashboard` (Collaborative React + Tailwind + React Flow dashboard)
- **Next up**: Build the Vector RAG Engine (`rag_engine/` with FAISS & CWE corpus) and LangGraph agent workflow (`agent/`).

## Key Decisions Log
- **Team Responsibilities & Branching**:
  - **Lead (`main`)**: Whole backend API + repo ingestion + CodeBERT model + FAISS RAG + LangGraph agent + baseline frontend.
  - **Friend 2 (`feature/ast-graph-parser`)**: AST parser (`ast_slicer.py`) + NetworkX call graph (`graph_builder.py`).
  - **Friends 3 & 4 (`feature/frontend-dashboard`)**: Collaborative React + Vite + Tailwind CSS + React Flow dashboard.
- **Backend & Schemas**: Central Pydantic schemas in `backend/schemas.py` are the single source of truth for both the parser output and the frontend UI.
- **Trained Model**: `microsoft/codebert-base` (125M parameters) — fits RTX 3050 VRAM (4GB-8GB).
- **Vector DB & Embeddings (for RAG)**: **FAISS** (local file-based index) + `sentence-transformers` (`all-MiniLM-L6-v2`) for local zero-cost search over CVE/CWE/OWASP corpus.
- **Agent Framework**: **LangGraph** (StateGraph DAG) for deterministic multi-step audit flow.

## Progress Log
### [2026-10-02] — Phase 0 Backend Foundation Complete
- Implemented `backend/requirements.txt` with FastAPI, Uvicorn, Pydantic, GitPython, and NetworkX.
- Implemented `backend/schemas.py` with comprehensive Pydantic models (`AuditRequest`, `Finding`, `GraphNode`, `GraphEdge`, `DependencyGraph`, `AuditResult`, `TaskStatusResponse`, `HealthResponse`).
- Implemented `backend/services/ingestor.py` with shallow git cloning (`--depth 1`), safe zip extraction (Zip Slip mitigation), and multi-language file scanner.
- Implemented `backend/services/task_manager.py` with thread-safe async task tracking (0-100% progress).
- Implemented `backend/routers/audit.py` with `/api/audit`, `/api/status/{task_id}`, `/api/report/{audit_id}`, and `/api/sample-report`.
- Implemented `backend/main.py` with CORS middleware and `/api/health`.
- Verified 100% test pass via `backend/tests/verify_backend.py`.

### [2026-10-02] — Team Division & Branch Strategy Refinement
- Updated roadmap to 3-branch structure: `main` (Backend + AI + Lead), `feature/ast-graph-parser` (Friend 2), `feature/frontend-dashboard` (Friends 3 & 4 collaborative).
- Synchronized `Phases.md`, `instructions.md`, and `Memory.md`.
