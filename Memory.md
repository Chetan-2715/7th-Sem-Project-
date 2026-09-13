# Memory.md — Progress Log

> This file is the AI's persistent context across sessions/tools. Update it after every meaningful chunk of work — don't wait until the end of a session. Keep entries brief and factual (what was done, what decided, what's next) rather than re-explaining the whole project each time.

## How to use this file
- At the start of any new session/chat, read this file first before touching code.
- After completing a task, append a new dated entry below — don't rewrite history.
- If a decision changes something in PRD.md / Architecture.md / Rules.md / Phases.md / Design.md, note it here AND update that source file.
- Keep the "Current Status" section at the top always up to date — this is the fastest thing to read.

---

## Current Status
- **Phase**: Phase 0 — Setup & Decisions (In Progress)
- **Last worked on**: Architectural decisions finalized & conceptual explanation prepared for user.
- **Next up**: Project skeleton setup (backend FastAPI + frontend React) and dataset initialization.

## Key Decisions Log
- **Target Languages / Scope**: Multi-tier repository scanning: Python (native AST), C/C++ (Devign classifier), JS/TS/React frontend (XSS, secret leaks), and `tree-sitter` for universal function chunking.
- **Report & UI Features**: Pinpoint exact file paths & line numbers (`filename.py:L42-L58`), side-by-side replacement code diff view (vulnerable vs fixed snippet), grounded CWE/CVE citations, and interactive dependency risk graph.
- **Trained Model**: `microsoft/codebert-base` (125M parameters) — lightweight, highly accurate for code vulnerability classification, and easily fits inside RTX 3050 VRAM (4GB-8GB).
- **Classifier Granularity**: Function-level chunking (matches Devign dataset and RAG context window size).
- **Agent Orchestration**: **LangGraph** chosen for explicit StateGraph pipeline control, predictable step execution, and real-time state streaming to UI.
- **Code Knowledge Graph**: Lightweight AST import/call mapping into a NetworkX graph, returned to frontend for interactive visualization using React Flow.
- **Vector DB & Embeddings (for RAG)**: **FAISS** (100% free, local Python package, file-based index) + `sentence-transformers` (`all-MiniLM-L6-v2`, ~80MB) for local, zero-cost semantic search over CVE/CWE/OWASP corpus.
- **LLM Agent Provider**: Compatible with any OpenAI-like API (**OpenRouter**, **NVIDIA NIM**, **Groq**, **Gemini**) or **100% offline local Ollama** (e.g. `qwen2.5-coder:1.5b` or `llama3.2:3b` running on RTX 3050). An API key is NOT mandatory!

## Progress Log
### [2026-08-29] — Project kickoff & Architectural Alignment
- Reviewed user's PRD.md, Architecture.md, Rules.md, Phases.md, Design.md, Memory.md.
- Adopted project documentation format as canonical project spec.
- Finalized key architectural decisions: Python target, function-level granularity, LangGraph agent framework, NetworkX call graph.

---

## Known Issues / Open Questions
- Dataset download: CodeXGLUE Devign C/C++ dataset needs to be downloaded/processed in `ml_pipeline`.
- Seed CVE/CWE corpus format needs to be populated in `backend/app/rag/corpus/`.

