# AI Workflow & Implementation Instructions 🤖

Welcome AI Assistant! This document contains the **strict workflow guidelines** for developing, testing, and reviewing components in the **Codebase Architecture & Risk Auditor** project repository.

When any AI coding assistant (Antigravity, Claude, ChatGPT, Cursor, etc.) works on this project, it **MUST** read and adhere to all the rules below before executing any code changes.

---

## 🛑 MANDATORY ENFORCEMENT RULES FOR ALL DEVELOPERS & AI ASSISTANTS

### 1. 📂 Root Directory Enforcement
- **Crucial:** Confirm that your current working directory is the **cloned repository root directory** (`D:\7th SEM MAJOR` or repository root).
- **DO NOT** execute commands from parent folders or arbitrary subdirectories.
- All Python module executions must use root-relative paths (e.g., `python -m backend.main` or `python agent/tests/verify_agent.py`).

### 2. 🛡️ Git Hygiene: Strictly Never Push Secrets, Packages, or Checkpoints
- Check `.gitignore` before every commit.
- The following directories and files must **NEVER** be staged or pushed to GitHub:
  - `.env` (Never push API keys! Use `.env.example` as a template).
  - `venv/`, `.venv/`, `env/` (Python virtual environments).
  - `node_modules/`, `frontend/node_modules/` (Node packages).
  - `data/` (Raw dataset splits).
  - `ml_pipeline/checkpoints/` (Heavy binary weights).
  - `__pycache__/`, `.pytest_cache/`, `dist/`, `frontend/dist/`.
  - Binary office documents (`*.docx`, `*.pptx`, `*.pdf`).
- Never run `git add .` blindly. Only stage verified source files!

### 3. 🔑 Environment Configuration & API Keys
- Duplicate `.env.example` to create your local `.env`:
  ```bash
  cp .env.example .env
  ```
- Set your Google Gemini API key:
  ```env
  GEMINI_API_KEY=your_gemini_api_key_here
  ```
- **Note**: The platform includes a built-in deterministic local fallback synthesizer. If no API key is provided or quota limits are hit, the system will automatically synthesize context-aware fixes without failing.

### 4. ⚡ Parallelized AI Fix Synthesis Guidelines
- The AI fix synthesizer (`agent/nodes.py`) uses `concurrent.futures.ThreadPoolExecutor(max_workers=5)` to accelerate patch generation.
- Never increase the worker count beyond 5 to avoid triggering provider rate limits (HTTP 429).
- All remediation signatures are cached in-memory (`_fix_cache`) during each audit run to prevent duplicate API requests for identical code patterns.

### 5. 🧪 Polyglot Syntax & Input Testing
- The platform supports four ingestion modalities:
  1. **GitHub Repository**: Clone and audit a public Git repo.
  2. **ZIP Archive**: Upload and unpack a zipped codebase.
  3. **Single File**: Audit an isolated Python, JS, Java, or C/C++ file.
  4. **Raw Code Snippet**: Audit arbitrary code snippets with automatic language detection.
- Polyglot syntax validation covers Python (`ast.parse`), JavaScript (`node vm.Script`), and Java/C/C++ delimiter and semicolon balancing mapped to **CWE-754**.

---

## 👥 SYSTEM ARCHITECTURE & ROLES

```
                      ┌────────────────────────────────────────┐
                      │              origin/main               │
                      │   (Team Lead: Backend, ML, RAG, Agent)  │
                      └───────┬────────────────────────┬───────┘
                              │                        │
                              ▼                        ▼
        ┌───────────────────────────┐    ┌───────────────────────────┐
        │ feature/ast-graph-parser  │    │ feature/frontend-dashboard│
        │       (Teammate 2)        │    │    (Teammates 3 & 4)      │
        │ • AST Function Slicing    │    │ • React + Vite + Tailwind │
        │ • NetworkX Directed Graph │    │ • Health Score Gauge Dial │
        │ • Blast Radius Analysis   │    │ • React Flow Visualizer   │
        └───────────────────────────┘    └───────────────────────────┘
```

### 🌿 Master Pipeline (`main`)
- **FastAPI REST Server:** Routes (`/api/audit`, `/api/audit-upload`, `/api/audit-file`, `/api/audit-raw`, `/api/audit/{task_id}/status`, `/api/audit/{task_id}/report`).
- **Pydantic v2 Schemas:** [`backend/schemas.py`](../backend/schemas.py).
- **Ingestion & Security:** Shallow git cloner and path traversal-safe zip extractor (`backend/services/ingestor.py`).
- **Vector RAG Engine:** Local FAISS vector index (`rag_engine/`) over MITRE CWE Top 25 & OWASP Top 10.
- **LangGraph Agent:** Stateful DAG workflow (`agent/`) synthesizing side-by-side patch diffs.
- **CodeBERT Model:** Trained weights and inference engine (`ml_pipeline/`).

---

## 🚀 HOW TO RUN THE SERVERS LOCALLY

### 1. Start the FastAPI Backend Server
```powershell
.\venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger API docs available at: `http://localhost:8000/docs`

### 2. Start the React Frontend Dev Server
```powershell
cd frontend
npm run dev -- --host
```
Frontend accessible at: `http://localhost:5173`

---

## 🧪 VERIFICATION COMMANDS

Run the automated test suites to ensure full system health:
```powershell
# 1. Verify AST Parser and NetworkX Graph
python parser_engine/tests/test_parser.py

# 2. Verify FAISS Vector RAG Engine
python rag_engine/tests/verify_rag.py

# 3. Verify LangGraph Agent Workflow
python agent/tests/verify_agent.py

# 4. Verify FastAPI Backend Endpoints
python -m pytest backend/tests/test_backend.py
```
