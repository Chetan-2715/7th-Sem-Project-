# Memory.md — Progress Log

> This file is the AI's persistent context across sessions/tools. Update it after every meaningful chunk of work — don't wait until the end of a session. Keep entries brief and factual (what was done, what decided, what's next) rather than re-explaining the whole project each time.

## How to use this file
- At the start of any new session/chat, read this file first before touching code.
- After completing a task, append a new dated entry below — don't rewrite history.
- If a decision changes something in PRD.md / Architecture.md / Rules.md / Phases.md / Design.md, note it here AND update that source file.
- Keep the "Current Status" section at the top always up to date — this is the fastest thing to read.

---

## Current Status
- **Phase**: Phase 0 — Setup & Backend Foundation (In Progress)
- **Active Task**: Team Lead building the Whole Backend (FastAPI, schemas, ingestion, routes), ML classifier, FAISS RAG, LangGraph agent, and baseline test UI on `main`.
- **Parallel Branches**:
  - Friend 2: `feature/ast-graph-parser` (AST parser & NetworkX graph)
  - Friends 3 & 4: `feature/frontend-dashboard` (Collaborative React + Tailwind + React Flow dashboard)
- **Next up**: Build `backend/schemas.py`, `backend/main.py`, `backend/services/ingestor.py`, and `backend/requirements.txt`.

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
### [2026-10-02] — Team Division & Branch Strategy Refinement
- Updated roadmap to 3-branch structure: `main` (Backend + AI + Lead), `feature/ast-graph-parser` (Friend 2), `feature/frontend-dashboard` (Friends 3 & 4 collaborative).
- Synchronized `Phases.md`, `instructions.md`, and `Memory.md`.
- Ready to begin Phase 0 Backend implementation on `main`.
