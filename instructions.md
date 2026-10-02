# AI Workflow & Implementation Instructions 🤖

Welcome AI Assistant! This document contains the **strict, mandatory workflow guidelines** for developing components in the **Codebase Architecture & Risk Auditor** project repository.

When any AI coding assistant (Antigravity, Claude, ChatGPT, Cursor, etc.) opens this project, it **MUST** read and adhere to all the rules below before executing any code changes.

---

## 🛑 MANDATORY ENFORCEMENT RULES FOR ALL AI ASSISTANTS

### 1. 📂 Root Directory Enforcement
- **Crucial:** Confirm that your current working directory (`cwd`) is the **cloned repository root directory** (e.g., `7th-Sem-Project-` or your project root).
- **DO NOT** execute commands from parent folders (e.g., `C:/projects/`) or nested subfolders (e.g., `backend/` or `frontend/`).
- All module executions must use root-relative paths (e.g., `python -m backend.main` or `python parser_engine/tests/test_parser.py`).

### 2. 🚫 STRICT TASK BOUNDARIES (DO NOT TOUCH OTHER FOLDERS)
- **If you are Friend 2 (AST & Call-Graph Lead):**
  - You **ONLY** modify files inside `parser_engine/`.
  - You are **STRICTLY FORBIDDEN** from modifying `backend/`, `rag_engine/`, `agent/`, `ml_pipeline/`, or `frontend/`.
- **If you are Friends 3 & 4 (Frontend UI/UX Team):**
  - You **ONLY** modify files inside `frontend/`.
  - You are **STRICTLY FORBIDDEN** from modifying `backend/`, `rag_engine/`, `agent/`, `ml_pipeline/`, or `parser_engine/`.
- **The Team Lead handles:** `backend/`, `rag_engine/`, `agent/`, `ml_pipeline/`, and `main` branch merging.

### 3. 🚫 NEVER TRAIN THE MODEL (NO GPU ENVIRONMENT)
- The **CodeBERT (125M parameter)** neural model has **ALREADY BEEN TRAINED** by the Team Lead on a local dedicated **NVIDIA RTX 3050 GPU** (achieving **87.50% Accuracy** and **0.8571 F1-Score** on the CodeXGLUE Devign dataset).
- Teammate systems do **NOT** have this GPU environment configured.
- **DO NOT RUN `python ml_pipeline/train.py` OR ATTEMPT MODEL RETRAINING.** The existing backend and agent automatically utilize the saved SafeTensors weights or built-in heuristic fallbacks.

### 4. 🛡️ GIT HYGIENE: NEVER PUSH PACKAGES, VENVS, OR CHECKPOINTS
- Check `.gitignore` before every commit.
- The following directories and files must **NEVER** be staged or pushed to GitHub:
  - `venv/`, `.venv/`, `env/` (Python virtual environments)
  - `node_modules/` (Node packages)
  - `data/` (Raw dataset splits)
  - `ml_pipeline/checkpoints/` (Heavy binary weights)
  - `.env` (Secret files)
  - `__pycache__/`, `.pytest_cache/`, `dist/`
- Never run `git add .` blindly. Only stage your specific source files!

### 5. 🧪 MANDATORY VERIFICATION BEFORE CLAIMING COMPLETION
- Writing code without running it is **strictly forbidden**.
- You **MUST** write and execute an automated verification script or run manual verification commands:
  - For `parser_engine/`: Run `python parser_engine/tests/test_parser.py` and ensure an exit code of `0` with verified nodes and edges.
  - For `frontend/`: Verify dashboard rendering and API communication against `http://localhost:8000/api/sample-report`.
- **Never claim a task is completed until you have verified the execution output in your terminal.**

### 6. 🌿 BRANCH ISOLATION & GIT WORKFLOW
- **DO NOT** commit directly to `main`.
- Create and checkout your designated branch:
  - **Friend 2:** `git checkout -b feature/ast-graph-parser`
  - **Friends 3 & 4:** `git checkout -b feature/frontend-dashboard`
- Push **ONLY** to your specific branch:
  - Friend 2: `git push -u origin feature/ast-graph-parser`
  - Friends 3 & 4: `git push -u origin feature/frontend-dashboard`

---

## 👥 TEAM RESPONSIBILITIES & BRANCH ARCHITECTURE

```
                      ┌────────────────────────────────────────┐
                      │              origin/main               │
                      │   (Team Lead: Backend, ML, RAG, Agent)  │
                      └───────┬────────────────────────┬───────┘
                              │                        │
                              ▼                        ▼
        ┌───────────────────────────┐    ┌───────────────────────────┐
        │ feature/ast-graph-parser  │    │ feature/frontend-dashboard│
        │       (Friend 2)          │    │      (Friends 3 & 4)      │
        │ • AST Function Slicing    │    │ • React + Vite + Tailwind │
        │ • NetworkX Directed Graph │    │ • Health Score Gauge Dial │
        │ • Blast Radius Analysis   │    │ • React Flow Visualizer   │
        └───────────────────────────┘    └───────────────────────────┘
```

### 🌿 Branch 1: `main` (Team Lead)
- **FastAPI REST Server:** Routes (`/api/audit`, `/api/status/{task_id}`, `/api/report/{audit_id}`, `/api/sample-report`).
- **Pydantic v2 Schemas:** [`backend/schemas.py`](backend/schemas.py) (The single source of truth for all data contracts).
- **Ingestion & Security:** Shallow git cloner and Zip Slip-safe zip extractor (`backend/services/ingestor.py`).
- **Vector RAG Engine:** Local FAISS vector index (`rag_engine/`) over MITRE CWE Top 25 & OWASP Top 10.
- **LangGraph Agent:** Stateful DAG workflow (`agent/`) synthesizing side-by-side patch diffs.
- **CodeBERT Model:** Trained weights and inference engine (`ml_pipeline/`).

### 🌿 Branch 2: `feature/ast-graph-parser` (Friend 2)
- **`parser_engine/ast_slicer.py`**:
  - Extract discrete function blocks with exact line numbers (`filename.py:L42-L58`).
  - Calculate cyclomatic complexity and argument count.
- **`parser_engine/graph_builder.py`**:
  - Build `networkx.DiGraph` representing function calls, cross-file imports, and class inheritances.
  - Return JSON strictly adhering to the schema in `backend/schemas.py`:
    ```json
    {
      "nodes": [{"id": "file.py:func", "label": "func()", "type": "function", "risk": "Medium"}],
      "edges": [{"source": "main.py:entry", "target": "file.py:func", "relationship": "calls"}]
    }
    ```
  - Implement **blast radius** calculation for vulnerable nodes.
- **`parser_engine/tests/test_parser.py`**:
  - Standalone verification script asserting that functions are sliced correctly and the NetworkX graph exports valid nodes/edges.

### 🌿 Branch 3: `feature/frontend-dashboard` (Friends 3 & 4)
- **`frontend/`**:
  - Build a responsive dark-mode developer dashboard (React + Vite + Tailwind CSS or enhanced vanilla JS/CSS) styled in `#0D1117`.
  - **Audit Form:** Accept GitHub repository URL or `.zip` file upload.
  - **Real-Time Polling:** Poll `GET /api/status/{task_id}` for progress (0%–100%).
  - **Security Health Score Dial:** Visual SVG gauge showing score (0–100).
  - **Filterable Findings Table:** Filter by severity (Critical, High, Medium, Low) and CWE/OWASP categories.
  - **Side-by-Side Diff Viewer:** Split viewer showing vulnerable code vs. synthesized fix.
  - **React Flow / Cytoscape Graph:** Interactive canvas visualizing call-graph nodes and edges.
  - Connect to `http://localhost:8000/api/sample-report` for instant mock testing without waiting for full repo scans.

---

## 📋 STEP-BY-STEP EXECUTION PROTOCOL FOR AI ASSISTANTS

1. **Step 1: Context Ingestion**
   - Read [`README.md`](README.md), [`INSTRUCTIONS.md`](INSTRUCTIONS.md), and [`backend/schemas.py`](backend/schemas.py).
   - Identify your exact assigned role and constraints.
2. **Step 2: Environment Check**
   - Confirm current working directory is the repository root.
   - Run `git status` to verify working branch.
3. **Step 3: Branch Creation**
   - Switch to your feature branch (`git checkout -b feature/<branch-name>`).
4. **Step 4: Implementation**
   - Write clean, modular, typed code **ONLY** inside your assigned directory (`parser_engine/` or `frontend/`).
5. **Step 5: Rigorous Verification**
   - Execute test scripts in the terminal.
   - Confirm terminal exit code is `0` and all assertions pass.
6. **Step 6: Git Hygiene Check & Push**
   - Inspect `git status`. Ensure `venv/`, `node_modules/`, `checkpoints/`, or temporary files are NOT staged.
   - Commit only your source files.
   - Push to your feature branch:
     ```bash
     git push -u origin feature/<branch-name>
     ```
7. **Step 7: Notify Team Lead**
   - Provide summary of verified code and announce readiness for Pull Request review into `main`.
