# Rules.md — Boundaries for AI-Assisted Development

## General Principles
- Favor working, demoable code over exhaustive feature coverage. This is a scoped academic project, not a production SaaS.
- Never silently change the architecture defined in Architecture.md — if a change is needed, flag it explicitly and explain why before proceeding.
- Always check Memory.md before starting work in a new session, and update it after completing any meaningful chunk of work.

## Libraries & Tools
**Use:**
- Backend: FastAPI, Pydantic, GitPython, `tree-sitter` or `ast`, `sentence-transformers`, Chroma or FAISS, LangGraph or CrewAI, PyTorch/scikit-learn/HuggingFace `transformers`
- Frontend: React (Vite), Tailwind CSS, Axios or fetch for API calls
- Prefer open-source, self-hostable components over paid APIs where the difference in effort is small.

**Avoid unless explicitly approved:**
- Heavy, all-in-one AI app frameworks that obscure what's actually happening (e.g., no-code agent builders) — the point of this project is demonstrating real engineering.
- Paid/rate-limited APIs as a hard dependency for core functionality (fine for optional enhancement, not for the core pipeline).
- Executing untrusted repository code directly (no `eval`/`exec` of cloned repo contents, no running arbitrary scripts from the analyzed repo).
- New dependencies that aren't listed above without flagging them first.

## Error Handling
- Every external call (repo clone, model inference, vector DB query, LLM call) must have explicit error handling — no silent failures.
- If repo cloning fails (private repo, invalid URL, too large), return a clear user-facing error, not a stack trace.
- If the classifier or RAG layer returns low-confidence/empty results, the agent should say so plainly in the report rather than fabricating a finding.
- Log errors with enough context to debug (which stage failed, which file/repo) but never log full repo contents or secrets.

## Security & Safety
- Never execute code from the analyzed repository — only static analysis (parsing, classification) is allowed.
- Never send full repo contents to a third-party API without the user's awareness — if using an external LLM API, document what data leaves the system.
- Don't hardcode API keys/secrets in source — use environment variables and add `.env` to `.gitignore`.

## Agent Behavior
- The agent's tool set must stay small and explicit (e.g., `run_classifier`, `retrieve_docs`, `correlate_findings`, `generate_report`) — no open-ended "do anything" tools.
- The agent should never claim a finding is grounded in a source it didn't actually retrieve — every citation in the report must trace back to a real retrieved document.
- The agent should not auto-modify or commit changes to the analyzed repository — output is a report only, not an automated fix.

## Scope Discipline
- Before adding a new feature not listed in PRD.md or the current Phase (see Phases.md), pause and confirm it's actually needed.
- Multi-language support, CI/CD integration, and auto-fix are explicitly out of scope for v1 — don't build toward them prematurely.

## Code Style
- Python: follow PEP8, type-hint function signatures, keep functions single-purpose.
- React: functional components with hooks, keep components small and composable.
- Write docstrings/comments explaining *why*, not just *what*, especially in the model and agent code — this matters for explaining the project in a viva.
