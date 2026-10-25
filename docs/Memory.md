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

### [2026-10-25] — Context-Aware Diff Controls & SQLite / os.popen Precision Fixes
- **Context-Aware DiffViewer Controls (`frontend/src/components/DiffViewer.jsx`)**:
  - Previously, "Jump to Change" and "Focus: Changes Only" were unconditionally rendered even on 2-line snippets where all lines were modified, causing confusion because clicking them had nothing to scroll or fold.
  - Added smart heuristics:
    - `Jump to Change`: Only displayed when `rows.length > 8` and `firstChangedIndex > 3` (when scrolling is actually necessary).
    - `Focus: Changes Only`: Only displayed when `unchangedCount >= 4` (when there are actual unchanged boilerplate lines to fold).
  - Isolated added comment rows (`# Grounded Fix...`) so they render as standalone added rows rather than being cross-paired with function signatures (`def lookup...`).
- **Precision Detection & Fix Synthesis (`agent/nodes.py`)**:
  - Extended SQL injection parameterized fix synthesis to handle SQLite and custom database handles (`db.execute`, `conn.execute`, `session.execute`) with `?` placeholders.
  - Added `os.popen` to OS Command Injection detection regex and structured `subprocess.run` patch synthesis.

### [2026-10-25] — Python Symbol / NameError Verifier & Map Suppression for Raw Code
- **Python Symbol & NameError Validation in `agent/nodes.py`**:
  - Previously, `priint("hello")` was syntactically valid in Python grammar (`ast.parse` succeeds) and went uncaught because grammar parsers do not evaluate runtime identifiers.
  - Implemented an AST symbol resolver and built-in typo detector in `check_polyglot_syntax`.
  - Discovers function calls to undefined identifiers and matches against Python standard built-ins (`COMMON_BUILTINS`) using `difflib.get_close_matches`.
  - Accurately catches: `Python NameError: name 'priint' is not defined (Did you mean: 'print'?) at line 1, col 1`.
  - Built-in grounded replacement synthesizer converts `priint(...)` -> `print(...)` with token-level diff highlighting.
- **Map Removal for Raw Code Snippets**:
  - Removed dependency map / React Flow generation for raw code snippets across backend (`parse_ast_node`, `compile_report_node`) and frontend (`App.jsx`, `DependencyFlow.jsx`).
  - Auditing single raw snippets now renders a clean, focused view with Health Score Gauge, Metric Cards, and Findings Table with Side-by-Side Diff, without empty or useless 1-node graphs.

### [2026-10-25] — Intelligent Line-by-Line Code Diff & Token Highlight Engine
- **LCS Line & Token Diff Engine in `frontend/src/components/DiffViewer.jsx`**:
  - Replaced full-block colored `<pre>` containers with an intelligent Longest Common Subsequence (LCS) line diff algorithm.
  - Unchanged lines are kept in clean, neutral syntax gray (`text-gray-400`), preventing visual fatigue on long code functions.
  - Removed/modified lines feature prominent rose banners (`bg-rose-950/40 border-l-4 border-rose-500`) with `-` gutter indicators.
  - Added/replacement lines feature prominent emerald banners (`bg-emerald-950/40 border-l-4 border-emerald-500`) with `+` gutter indicators.
  - Implemented token-level inline diffing (`renderInlineDiff`): for modified lines, prefix/suffix detection isolates the exact changed token (e.g. `innerHTML` vs `textContent`) and renders highlighted badges.
- **Productivity & Review Features**:
  - **Change Statistics & Jump**: Displays count badges (`-1 line`, `+2 lines`) and a "Jump to Change" auto-scroll button.
  - **Focus Mode ("Changes Only")**: Collapses unchanged boilerplate code into expandable fold bars (`@@ N unchanged lines hidden @@`).
  - **Dual View Modes**: Seamless toggle between `Split (Side-by-Side)` and `Unified (Git Diff)` streams.
  - **Line Numbering Sync**: Gutter displays true file line numbers (e.g. `L109–L142`) corresponding to AST slicing.
- **Reusability across UI**:
  - Integrated into both `frontend/src/components/FindingsTable.jsx` and `frontend/src/components/DependencyFlow.jsx`.

### [2026-10-25] — Hierarchical Folder Map & Interactive Drilldown Modal
- **Hierarchical Graph Engine in `frontend/src/components/DependencyFlow.jsx`**:
  - Replaced the unwieldy 800+ raw node graph with an aggregated **Folder Architecture View**.
  - Dynamically computes directory modules (e.g., `app/api/routes`, `app/db`, `alembic`, `(root)`), grouping files, functions, and vulnerabilities.
  - Aggregates cross-folder call and import dependencies with weighted, animated edges and invocation count badges.
  - Added security risk indicators on folder nodes: Red/Rose border and glow for Critical/High findings, Amber for Medium, and Emerald for Clean.
- **Interactive 2-Level Drilldown Modal**:
  - **Level 1 (Folder View)**: Displays folder path, files count, functions count, risk status, connected dependencies ("Calls into...", "Called by..."), file search filter, and cards for all files in the folder.
  - **Level 2 (File View)**: Breadcrumb navigation (`Map > 📁 Folder > 📄 File`), back button, search filter, and list of all functions with exact line bounds (`L42-L58`) and risk scores.
  - **In-Modal Vulnerability Diffs**: If a function has an associated security finding, it displays an alert card with the CWE description, original vulnerable code, and recommended replacement fix with a one-click `Copy Fix` button.
  - **Dual View Modes**: Added switcher between `📁 Folders Architecture` (default clean view) and `🌐 Micro-Graph` (detailed raw node view).
- **Gemini 2.5 Flash Latency & Thinking Optimization**:
  - Configured `thinkingConfig: {"thinkingBudget": 0}` in `agent/llm_engine.py` to eliminate thinking-token overhead.
  - Increased `timeout=12` and `maxOutputTokens=2048` to guarantee complete, uninterrupted code replacements without timeouts.

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
