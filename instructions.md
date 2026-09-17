# AI Workflow & Implementation Instructions 🤖

Welcome AI Assistant! This document contains the mandatory workflow guidelines for developing components in the **Codebase Architecture & Risk Auditor** project repository.

---

## 📌 STEP 1: Repository Context & Protocol Inspection
1. Clone or pull the latest changes from the official GitHub repository:
   ```bash
   git clone https://github.com/Chetan-2715/7th-Sem-Project-.git
   cd 7th-Sem-Project-
   git pull origin main
   ```
2. Inspect the core specification files to understand the project architecture, boundaries, and design system before writing any code:
   - [`PRD.md`](file:///d:/7th%20SEM%20MAJOR/PRD.md) — Vision, scope, target users, and core requirements.
   - [`Architecture.md`](file:///d:/7th%20SEM%20MAJOR/Architecture.md) — System flow, folder structure, API schemas, and tech stack choices.
   - [`Design.md`](file:///d:/7th%20SEM%20MAJOR/Design.md) — UI design tokens, dark mode palette (`#0D1117`), typography, layout principles.
   - [`Phases.md`](file:///d:/7th%20SEM%20MAJOR/Phases.md) — Sequential build roadmap and milestone definitions.
   - [`Rules.md`](file:///d:/7th%20SEM%20MAJOR/Rules.md) — Engineering guidelines, error handling, security constraints, and forbidden practices.
   - [`Memory.md`](file:///d:/7th%20SEM%20MAJOR/Memory.md) — Living log of completed work, decisions, and system state.

---

## 📌 STEP 2: Branch Creation & Git Isolation
Do **NOT** commit directly to `main`. Create and checkout your role-specific feature branch:
- **AST & Call-Graph Lead:** `git checkout -b feature/ast-graph-parser`
- **FastAPI Backend Lead:** `git checkout -b feature/fastapi-backend`
- **React Frontend Lead:** `git checkout -b feature/frontend-dashboard`
- **AI / RAG / Agent Lead:** `git checkout -b feature/ai-rag-agent` (or `main`)

---

## 📌 STEP 3: Phase Audit & Dependency Check
1. Read `Phases.md` and `Memory.md` to verify the current status of the codebase.
2. Confirm if prerequisite phases or data contracts (Pydantic schemas, folder structures) are completed.
3. Identify the exact phase tasks assigned to your role.

---

## 📌 STEP 4: Code Implementation & Rigorous Testing
1. Write clean, modular, production-ready code in your designated folder (`backend/`, `frontend/`, `parser_engine/`, `ml_pipeline/`, or `rag_engine/`).
2. Follow all guidelines in `Rules.md` (e.g., explicit error handling, PEP8/React hooks standards, no hardcoded secrets).
3. **Mandatory Testing:** Run unit tests or local dev servers (`pytest`, `uvicorn`, `npm run dev`) to verify your code works cleanly without breaking existing logic or blocking other team members.

---

## 📌 STEP 5: Update Living Documentation & State
Upon successful verification:
1. Update `Memory.md` with:
   - What was implemented (modules, functions, routes, or UI components).
   - Verification / test results.
   - Any API schema details or setup instructions for the team.
2. Mark completed tasks in `Phases.md`.

---

## 📌 STEP 6: Clean Up & Push Feature Branch
1. Verify build artifacts, virtual environments (`.venv`), `__pycache__`, `node_modules/`, and temp files are in `.gitignore`.
2. Commit your work with a clear descriptive message:
   ```bash
   git add <your_modified_files> Memory.md Phases.md .gitignore
   git commit -m "Complete <your_feature_name> and update Memory.md"
   git push -u origin feature/<your_branch_name>
   ```

---

## 📌 STEP 7: Final Teammate Notification
Print a clear final summary for the user:
- What was built and verified.
- Instructions on how to run or test the code.
- Explicit prompt telling the teammate to notify the **Team Lead (main branch handler)** that branch `feature/<your_branch_name>` is ready for review and merge into `main`.
