# Memory.md — Progress Log

> This file is the AI's persistent context across sessions/tools. Update it after every meaningful chunk of work — don't wait until the end of a session. Keep entries brief and factual (what was done, what decided, what's next) rather than re-explaining the whole project each time.

## How to use this file
- At the start of any new session/chat, read this file first before touching code.
- After completing a task, append a new dated entry below — don't rewrite history.
- If a decision changes something in PRD.md / Architecture.md / Rules.md / Phases.md / Design.md, note it here AND update that source file.
- Keep the "Current Status" section at the top always up to date — this is the fastest thing to read.

---

## Current Status
- **Phase**: Phase 0 (Backend), Phase 1-3 (RAG & Dataset), Phase 4 (LangGraph Agent), Phase 6 (Baseline UI) — ALL COMPLETED!
- **Active Task**: All backend, RAG, agent, and ML training scripts are written and verified. Ready for user to run training in terminal.
- **Parallel Branches**:
  - Friend 2: `feature/ast-graph-parser` (AST parser & NetworkX graph)
  - Friends 3 & 4: `feature/frontend-dashboard` (Collaborative React + Tailwind + React Flow dashboard)
- **Next up**: User runs `python ml_pipeline/train.py` in terminal when ready.

## Key Decisions Log
- **Team Responsibilities & Branching**:
  - **Lead (`main`)**: Whole backend API + repo ingestion + CodeBERT model + FAISS RAG + LangGraph agent + baseline frontend.
  - **Friend 2 (`feature/ast-graph-parser`)**: AST parser (`ast_slicer.py`) + NetworkX call graph (`graph_builder.py`).
  - **Friends 3 & 4 (`feature/frontend-dashboard`)**: Collaborative React + Vite + Tailwind CSS + React Flow dashboard.
- **RAG Knowledge Base**: Expanded to cover the full **MITRE CWE Top 25** and OWASP standards.
- **Trained Model**: `microsoft/codebert-base` (125M parameters) with PyTorch / Hugging Face sequence classification head. Mixed precision (`fp16=True`) enabled for RTX 3050 GPU.
- **Dataset Storage**: `data/devign/` is strictly gitignored to protect GitHub repo from large binaries.

## Progress Log
### [2026-10-02] — ML Pipeline & Expanded RAG Complete
- Expanded `rag_engine/corpus/cwe_owasp_knowledge_base.json` to the MITRE CWE Top 25.
- Created `ml_pipeline/download_dataset.py` with automated CodeXGLUE Devign dataset fetching.
- Created `ml_pipeline/dataset.py` implementing PyTorch tokenization for CodeBERT.
- Created `ml_pipeline/model.py` wrapping `microsoft/codebert-base` with classification head.
- Created `ml_pipeline/train.py` featuring RTX 3050 CUDA detection, fp16 acceleration, and live terminal progress.
- Created `ml_pipeline/inference.py` for testing individual code snippets.
- Maintained 100% clean git tree (data and checkpoints ignored).

### [2026-10-02] — Vector RAG, LangGraph Agent & Baseline UI Complete
- Built FAISS Vector RAG engine and LangGraph StateGraph DAG.
- Connected agent orchestrator to FastAPI backend worker.
- Built baseline test UI in `frontend/index.html` mounted at `http://localhost:8000/`.

### [2026-10-02] — Phase 0 Backend Foundation Complete
- Implemented FastAPI backend, schemas, ingestor, task manager, and test suites.
