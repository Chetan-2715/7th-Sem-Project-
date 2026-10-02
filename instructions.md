# AI Workflow & Implementation Instructions 🤖

Welcome AI Assistant! This document contains the mandatory workflow guidelines and dependency chain rules for developing components in the **Codebase Architecture & Risk Auditor** project repository.

---

## 🔗 TEAM BRANCHES & RESPONSIBILITY DIVISION

### 🌿 Branch 1: `main` (Handled by Team Lead)
- **Whole Backend:** FastAPI REST server, Pydantic schemas (`backend/schemas.py`), repository ingestion service, background task manager, API routes (`/api/audit`, `/api/health`, `/api/status`, `/api/report`).
- **AI Models & Classifier:** Fine-tuned `microsoft/codebert-base` vulnerability classifier.
- **Vector RAG Engine:** Local FAISS vector index + `sentence-transformers` (`all-MiniLM-L6-v2`) on CWE/OWASP corpus.
- **Agent Workflow:** LangGraph StateGraph DAG agent (`Ingest` → `Scan` → `RAG` → `Synthesize` → `Report`).
- **Baseline Frontend:** Simple test frontend to verify end-to-end audit execution.

### 🌿 Branch 2: `feature/ast-graph-parser` (Handled by Friend 2)
- **AST Slicer:** Function extraction with exact line numbers (`filename.py:L42-L58`) using Python `ast` and `tree-sitter`.
- **Call-Graph Builder:** NetworkX directed dependency graph exporting `{ nodes: [...], edges: [...] }` JSON matching backend schemas.
- **Unit Tests:** `pytest` test suite in `tests/test_parser.py`.

### 🌿 Branch 3: `feature/frontend-dashboard` (Handled Collaboratively by Friends 3 & 4)
- **Modern Dashboard:** React (Vite) + Tailwind CSS dark-mode dashboard (`#0D1117`).
- **Visual Components:** Security Health Score dial (0–100), filterable findings table, side-by-side code diff viewer.
- **Graph Visualizer:** Interactive React Flow call-graph component rendering backend-provided dependency graph.
- **Polished UX:** Real-time audit progress bar, error handling, and citation modals.

---

## 📌 STEP 1: Repository Context & Protocol Inspection
1. Clone or pull the latest changes from the official GitHub repository:
   ```bash
   git clone https://github.com/Chetan-2715/7th-Sem-Project-.git
   cd 7th-Sem-Project-
   git pull origin main
   ```
2. Inspect the core specification files:
   - [`PRD.md`](file:///d:/7th%20SEM%20MAJOR/PRD.md) — Vision, scope, and core requirements.
   - [`Architecture.md`](file:///d:/7th%20SEM%20MAJOR/Architecture.md) — System flow, folder structure, API schemas, and tech stack choices.
   - [`Design.md`](file:///d:/7th%20SEM%20MAJOR/Design.md) — UI design tokens, dark mode palette (`#0D1117`), typography, layout principles.
   - [`Phases.md`](file:///d:/7th%20SEM%20MAJOR/Phases.md) — Sequential build roadmap and team dependency chain.
   - [`Rules.md`](file:///d:/7th%20SEM%20MAJOR/Rules.md) — Engineering guidelines, error handling, security constraints, and forbidden practices.
   - [`Memory.md`](file:///d:/7th%20SEM%20MAJOR/Memory.md) — Living log of completed work, decisions, and system state.

---

## 📌 STEP 2: Branch Creation & Git Isolation
Do **NOT** commit directly to `main` (unless you are the Team Lead). Create and checkout your assigned feature branch:
- **Friend 2 (AST & Call-Graph Lead):** `git checkout -b feature/ast-graph-parser`
- **Friends 3 & 4 (Collaborative Frontend Team):** `git checkout -b feature/frontend-dashboard`

---

## 📌 STEP 3: Phase Audit & Dependency Check
1. Read `Phases.md` and `Memory.md` to verify active phase tasks.
2. Confirm you are building against the schema contracts defined in `backend/schemas.py`.

---

## 📌 STEP 4: Accurate Implementation & Rigorous Testing
1. Write clean, modular, production-grade code in your designated folder (`parser_engine/` or `frontend/`).
2. Follow all guidelines in `Rules.md` (no hardcoded secrets, explicit exception handling, clean type hints).
3. **MANDATORY TESTING:** Run local tests (`pytest` for parser, `npm run dev` for frontend) to guarantee 100% correctness. Your code MUST NOT fail or break downstream work for other team members.

---

## 📌 STEP 5: Update Living Documentation & State
Upon successful testing:
1. Update `Memory.md` logging what was implemented, test results, and setup instructions.
2. Mark completed tasks in `Phases.md`.

---

## 📌 STEP 6: Clean Up & Push Feature Branch
1. **MANDATORY .GITIGNORE CHECK:** Ensure all unwanted build artifacts, virtual environments (`.venv`, `env/`), `__pycache__`, `node_modules/`, `dist/`, `.pytest_cache`, and temporary files are strictly included in `.gitignore`.
2. Commit your work with a descriptive commit message:
   ```bash
   git add <your_modified_files> Memory.md Phases.md .gitignore
   git commit -m "Complete <your_feature_name> and update Memory.md"
   git push -u origin feature/<your_branch_name>
   ```

---

## 📌 STEP 7: Final Teammate Notification
Print a clear final summary for the user:
- Summary of what was built and verified.
- Command-line instructions on how to test or run the module.
- Explicit prompt telling the teammate to notify the **Team Lead (main branch handler)** that branch `feature/<your_branch_name>` is ready to merge into `main`.
