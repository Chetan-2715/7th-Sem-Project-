# Phases.md — Build Roadmap, Completed Milestones & Team Execution

Each phase represents a verified, functional layer of the **Codebase Architecture & Risk Auditor** platform.

---

## 🔗 Team Role Division & Branching Strategy

- **Branch 1: `main` (Team Lead)**:
  - Core FastAPI async backend, Pydantic schemas (`backend/schemas.py`), multi-modal ingestion service (`backend/services/ingestor.py`).
  - CodeBERT deep learning classifier on CodeXGLUE Devign (`ml_pipeline/`).
  - FAISS Vector RAG engine with `all-MiniLM-L6-v2` (`rag_engine/`).
  - LangGraph StateGraph DAG orchestrator (`agent/`).
  - Polyglot syntax engine and parallelized Google Gemini 2.5 Flash patch synthesizer.
- **Branch 2: `feature/ast-graph-parser` (Teammate 2)**:
  - AST function slicer with exact line-range boundaries (`L42-L58`) in `parser_engine/ast_slicer.py`.
  - NetworkX directed dependency graph constructor in `parser_engine/graph_builder.py`.
- **Branch 3: `feature/frontend-dashboard` (Teammates 3 & 4)**:
  - Modern React 18 + Vite + Tailwind CSS dashboard (`#0D1117`).
  - Security Health Score dial, Metric cards, filterable findings table, side-by-side diff viewer, and React Flow interactive call graph.

---

## 📍 Milestones & Execution History

### ✅ Phase 0 — Backend Foundation & Data Schemas
- Built directory architecture (`backend/`, `agent/`, `ml_pipeline/`, `rag_engine/`, `parser_engine/`, `frontend/`).
- Defined Pydantic contracts in `backend/schemas.py`: `AuditRequest`, `AuditResult`, `Finding`, `GraphNode`, `GraphEdge`.
- Implemented FastAPI server in `backend/main.py` with CORS, `/api/health`, and async task worker.
- Created `backend/services/ingestor.py` with shallow Git cloning and ZIP decompression.

### ✅ Phase 1 — AST Function Slicer & NetworkX Call Graph
- Built `parser_engine/ast_slicer.py`: extracts discrete function boundaries, signatures, and line numbers (`filename.py:L42-L58`).
- Built `parser_engine/graph_builder.py`: utilizes `networkx.DiGraph` to map inter-module imports and call topologies.
- Validated via `parser_engine/tests/test_parser.py`.

### ✅ Phase 2 & 3 — CodeBERT Model & Local Vector RAG
- Fine-tuned `microsoft/codebert-base` (125M parameters) on the CodeXGLUE Devign vulnerability dataset using PyTorch with `fp16` mixed precision on NVIDIA RTX 3050.
- Built offline FAISS vector database (`rag_engine/vector_store.py`) indexing the complete **MITRE CWE Top 25** and **OWASP Top 10** knowledge base.
- Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) for sub-millisecond semantic similarity search.

### ✅ Phase 4 & 5 — LangGraph StateGraph DAG Orchestrator
- Implemented stateful LangGraph agent in `agent/orchestrator.py`:
  $$\text{Ingest} \longrightarrow \text{Scan} \longrightarrow \text{Retrieve} \longrightarrow \text{Synthesize} \longrightarrow \text{Report}$$
- Unified AST parsing, CodeBERT classification, FAISS retrieval, and AI patch generation.
- Formatted structured JSON output with precise line citations and replacement diffs.

### ✅ Phase 6 — Interactive React Dashboard & Visualizer
- Implemented responsive dark-mode dashboard in `frontend/src/` using React, Vite, and Tailwind CSS.
- Developed interactive components:
  - `HealthScoreGauge.jsx`: dynamic circular SVG score gauge.
  - `MetricCards.jsx`: high-visibility severity counters.
  - `FindingsTable.jsx`: expandable rows with CWE chips and markdown explanations.
  - `DiffViewer.jsx`: side-by-side original vs fixed code comparison.
  - `DependencyFlow.jsx`: React Flow dependency graph visualization.

### ✅ Phase 7 — Polyglot Ingestion & Auto-Language Detection
- Added 4 ingestion tabs: GitHub Repo, ZIP Archive, Single File, and Raw Code Snippet.
- Implemented auto-detection heuristic across 8+ programming languages (Python, JS, TS, Java, C, C++, PHP, SQL, Go, Rust).
- Added real-time detected language pill badge in the UI.

### ✅ Phase 8 — Concurrency Acceleration & Security Hardening
- **Polyglot Syntax Engine**: Integrated multi-language syntax checking (`ast.parse` for Python, Node.js `vm.Script` for JS, delimiter balancing and missing semicolon detection for Java/C/C++) categorized under **CWE-754**.
- **Rule Expansion**: Expanded vulnerability scanner to cover 18 CWE Top 25 & OWASP weakness categories.
- **Parallel Remediation Engine**: Accelerated AI fix generation with `ThreadPoolExecutor(max_workers=5)` and pattern signature caching, cutting audit latency from ~10 minutes to ~33 seconds.
- **Encoding & Parsing Hardening**: Handled UTF-8 BOM (`\ufeff`) sanitization and shielded code comments from improper syntax mutation.
- **Git & Environment Hygiene**: Created `.env.example`, protected `.env` credentials, and structured documentation into `docs/`.
