# Rules.md — Boundaries & Engineering Standards for Development

## General Principles
- Favor working, verified code with clear demonstration value.
- Never silently modify system architecture without updating `docs/Architecture.md` and logging the rationale in `docs/Memory.md`.
- Ground every security finding in verified knowledge base entries (MITRE CWE / OWASP). Hallucinated CVEs/CWEs are strictly prohibited.

---

## Technical Stack & Library Standards

### Approved Stack:
- **Backend**: FastAPI, Uvicorn, Pydantic, GitPython, `zipfile`.
- **Parsing & AST**: Python `ast`, Node.js `vm.Script`, delimiter matching heuristics, NetworkX (`nx.DiGraph`).
- **Deep Learning**: PyTorch, Hugging Face `transformers` (`microsoft/codebert-base`), safetensors.
- **RAG & Vector Retrieval**: Meta FAISS (`IndexFlatL2`), `sentence-transformers` (`all-MiniLM-L6-v2`).
- **Agent Workflow**: LangGraph (`StateGraph`), concurrent futures (`ThreadPoolExecutor`).
- **Generative AI Fixes**: Google Gemini 2.5 Flash via `google-genai` SDK with deterministic local fallback synthesizer.
- **Frontend**: React 18 (Vite), Tailwind CSS, Lucide icons, React Flow.

### Prohibited Patterns:
- Do NOT hardcode API keys or secrets in any source file. All keys must be read through `os.environ.get("GEMINI_API_KEY")` with a `.env` file that is strictly gitignored.
- Do NOT execute untrusted repository code. The platform performs static, neuro-symbolic, and AST analysis only; never run `eval()` or `exec()` on arbitrary user inputs.
- Do NOT push datasets (`data/`), model checkpoints (`ml_pipeline/checkpoints/`), virtual environments (`venv/`), or build artifacts (`node_modules/`, `dist/`).

---

## Concurrency & API Quota Protection
- When querying generative AI APIs (such as Gemini 2.5 Flash), use `ThreadPoolExecutor(max_workers=5)` to parallelize network I/O while preventing quota exhaustion.
- Cache remediation patterns (`_fix_cache`) to avoid redundant API requests for identical code signatures.
- Always implement a deterministic local fallback synthesizer so the system functions smoothly in offline or rate-limited environments.

---

## Error Handling & Resiliency
- Handle UTF-8 Byte Order Marks (`\xef\xbb\xbf` / `\ufeff`) cleanly using `utf-8-sig` encoding.
- Shield comments (`#`, `//`, `/*`, `*`) from being corrupted or converted to invalid syntax fixes.
- External operations (git cloning, ZIP extraction, model inference, vector queries) must include `try-except` wrappers returning clean user-facing error messages instead of raw stack traces.

---

## Code Quality & Documentation
- Python: PEP8 compliant, type hints on function signatures, modular single-purpose functions.
- React: Functional components with hooks, clear component separation, accessible color contrast.
- Maintain documentation integrity: all architectural updates must be documented in `docs/` and referenced in root `README.md`.
