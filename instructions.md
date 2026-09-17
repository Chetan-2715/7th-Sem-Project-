# AI Workflow & Implementation Instructions 🤖

Welcome AI Assistant! This document contains the mandatory workflow guidelines and dependency chain rules for developing components in the **Codebase Architecture & Risk Auditor** project repository.

---

## 🔗 MANDATORY TEAM DEPENDENCY CHAIN
Please understand your role in the development chain:
- **Friend 3 (FastAPI Backend Lead)** STARTS FIRST by creating `backend/schemas.py` with Pydantic JSON models (`AuditRequest`, `AuditResult`, `Finding`, `GraphNode`, `GraphEdge`). This defines the data contracts that Friend 2 and Friend 4 depend on!
- **Friend 2 (AST & Graph Lead)** builds `parser_engine/` ensuring graph output matches Friend 3's `GraphNode` & `GraphEdge` JSON schema.
- **Friend 4 (React Frontend Lead)** builds `frontend/` UI components using Friend 3's schemas with mock data in parallel.
- **Team Lead (AI Lead)** integrates CodeBERT + FAISS RAG + LangGraph into the backend once PRs are merged.

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
Do **NOT** commit directly to `main`. Create and checkout your role-specific feature branch:
- **AST & Call-Graph Lead:** `git checkout -b feature/ast-graph-parser`
- **FastAPI Backend Lead:** `git checkout -b feature/fastapi-backend`
- **React Frontend Lead:** `git checkout -b feature/frontend-dashboard`

---

## 📌 STEP 3: Phase Audit & Dependency Check
1. Read `Phases.md` and `Memory.md` to verify active phase tasks.
2. If you are Friend 3, ensure `backend/schemas.py` is defined first and pushed.
3. If you are Friend 2 or 4, confirm you are building against the schema contracts defined in `backend/schemas.py`.

---

## 📌 STEP 4: Accurate Implementation & Rigorous Testing
1. Write clean, modular, production-grade code in your designated folder (`backend/`, `frontend/`, or `parser_engine/`).
2. Follow all guidelines in `Rules.md` (no hardcoded secrets, explicit exception handling, clean type hints).
3. **MANDATORY TESTING:** Run local tests (`pytest`, Swagger UI `/docs`, `npm run dev`) to guarantee 100% correctness. Your code MUST NOT fail or break downstream work for other team members.

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
