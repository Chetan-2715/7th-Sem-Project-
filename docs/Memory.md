# Memory.md — Persistent Context & Progress Log

> This file maintains persistent context across sessions, documenting key technical decisions, current operational state, and recent milestones.

---

## Current Status
- **System State**: Fully operational end-to-end neuro-symbolic review platform.
- **Backend**: FastAPI async server running on `http://localhost:8000`.
- **Frontend**: React + Vite + Tailwind dashboard running on `http://localhost:5173`.
- **Active Capabilities**:
  - Multi-modal ingestion (GitHub URL, ZIP archive, single file, raw code snippet).
  - Polyglot language auto-detection (Python, JS, TS, Java, C, C++, PHP, SQL, Go, Rust).
  - Polyglot syntax validation (Python AST, Node.js vm.Script, delimiter balancing) under **CWE-754**.
  - 18 CWE Top 25 & OWASP vulnerability categories.
  - Offline FAISS Vector RAG grounding.
  - Parallel AI patch synthesis via Google Gemini 2.5 Flash (`ThreadPoolExecutor(max_workers=5)`) with remediation caching and offline fallback.
  - Clean documentation hierarchy organized in `docs/` with root `README.md`.

---

## Key Decisions & Architecture Log
1. **Parallel AI Patch Synthesis**:
   - Sequential LLM calls for 50 findings caused ~10-minute audit latency.
   - Replaced with `concurrent.futures.ThreadPoolExecutor(max_workers=5)` in `agent/nodes.py`.
   - Pattern and remediation signature caching eliminates redundant API requests for identical code patterns.
   - Reduced audit duration to ~33 seconds on a 50-finding test suite.
2. **Polyglot Syntax Engine (CWE-754)**:
   - Sytax errors in any supported language (Python `ast.parse`, JS Node.js `vm.Script`, Java/C/C++ delimiter matching & missing semicolons) are mapped to **CWE-754** (Improper Check for Unusual or Exceptional Conditions).
   - Prevents non-compilable code from escaping and grounds it with authoritative CWE documentation and Gemini replacement code.
3. **UTF-8 BOM Sanitization**:
   - Files with `\xef\xbb\xbf` (UTF-8 BOM) triggered false syntax errors (`invalid non-printable character U+FEFF`).
   - Resolved by using `utf-8-sig` encoding and `.lstrip('\ufeff')` in `ingestor.py` and `nodes.py`.
4. **Comment Protection**:
   - Comment lines (`#`, `//`, `/*`, `*`) are shielded from naive syntax fixers to prevent mutating non-executable comments into syntax corrections.
5. **Security & Git Cleanliness**:
   - `.env` strictly gitignored; `.env.example` committed.
   - Large datasets (`data/`), model weights (`ml_pipeline/checkpoints/`), virtualenvs (`venv/`), and build artifacts (`node_modules/`, `dist/`) remain strictly excluded.
   - All documentation consolidated into `docs/` with links in root `README.md`.

---

## Detailed Progress Log

### [2026-10-25] — Concurrency Acceleration & Polyglot Syntax Integration
- Implemented `check_polyglot_syntax` in `agent/nodes.py` covering Python, JavaScript, Java, C, and C++.
- Expanded vulnerability rules to cover all 18 CWE Top 25 & OWASP entries in `rag_engine/corpus/cwe_owasp_knowledge_base.json`.
- Implemented `ThreadPoolExecutor(max_workers=5)` and `_fix_cache` in `agent/nodes.py`, reducing 50-vulnerability audit runtime from ~10 mins to ~33 seconds.
- Added UTF-8 BOM (`\ufeff`) sanitization in `backend/services/ingestor.py` and `agent/nodes.py`.
- Shielded comment lines (`#`, `//`, `/*`, `*`) from syntax fixer corruption.
- Organized all repository `.md` specifications into `docs/` and updated `.gitignore`.

### [2026-10-23] — Multi-Modal Ingestion & Auto-Language Detection
- Implemented `/api/audit-upload`, `/api/audit-file`, and `/api/audit-raw` in `backend/routers/audit.py`.
- Built heuristic language auto-detection in `backend/services/ingestor.py` and `frontend/src/components/AuditInput.jsx`.
- Added detected language badge in the React dashboard.

### [2026-10-02] — ML Model Training & FAISS Vector RAG
- Fine-tuned `microsoft/codebert-base` on CodeXGLUE Devign dataset using RTX 3050 GPU (87.50% Accuracy, 0.8571 F1).
- Built local FAISS vector database indexing MITRE CWE Top 25 & OWASP with `all-MiniLM-L6-v2`.
- Built LangGraph StateGraph DAG agent in `agent/orchestrator.py`.
- Built full React + Vite + Tailwind CSS dashboard with React Flow dependency graph.
