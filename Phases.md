# Phases.md — Build Roadmap

Each phase should end in something runnable/demoable, even if minimal. Do not start a phase until the previous one is functionally complete.

## Phase 0 — Setup & Decisions
- Finalize target language(s) for v1 (recommend: Python-only to start, given dataset availability and your own skillset).
- Set up repo structure per Architecture.md.
- Set up backend (FastAPI skeleton) and frontend (React skeleton) that can talk to each other with a basic "hello world" round trip.
- Download and explore the chosen dataset (CodeXGLUE/Devign) — confirm it's usable and understand its label distribution.

## Phase 1 — Repo Ingestion & Parsing
- Implement repo cloning from a GitHub URL.
- Implement file-tree walking filtered to the target language.
- Implement function/chunk extraction (AST-based).
- Implement a basic dependency map (which file imports/calls which).
- Demo: given a repo URL, output a JSON list of parsed functions + a simple dependency map — no ML yet.

## Phase 2 — Trained Classifier
- Preprocess the dataset into model-ready format.
- Train a baseline classifier (start simple — e.g., XGBoost on extracted features or a small fine-tuned transformer).
- Evaluate on a held-out test split; record actual precision/recall/F1.
- Wire the trained model into inference: given parsed code chunks from Phase 1, output flagged items with category + confidence.
- Demo: given a repo, output a list of flagged functions with risk category and confidence score.

## Phase 3 — RAG Pipeline
- Collect and clean the CVE/CWE/OWASP corpus for retrieval.
- Build embeddings and populate the vector DB (Chroma/FAISS).
- Implement retrieval: given a flagged finding, return top-k relevant grounding documents.
- Demo: given a flagged item from Phase 2, show the retrieved supporting documentation.

## Phase 4 — Agent Orchestration
- Define the agent's tool set (classifier call, retrieval call, correlation logic, report generation).
- Implement the orchestration graph/chain (LangGraph or CrewAI): ingest → classify → retrieve → correlate → generate report.
- Implement severity scoring logic (rule-based to start; can be refined later).
- Demo: full pipeline runs end-to-end from repo URL to a structured JSON report, via a single backend call.

## Phase 5 — Backend API
- Wrap the full pipeline behind `POST /audit`, `GET /audit/{job_id}/status`, `GET /audit/{job_id}/report`.
- Add basic job tracking (in-memory or SQLite) so the frontend can poll progress.
- Add error handling per Rules.md.
- Demo: hit the API with a real repo URL via Postman/curl and get back a full report.

## Phase 6 — Frontend Dashboard
- Build the input form (repo URL + submit).
- Build a progress/status view while the audit runs.
- Build the results dashboard: severity-ranked findings table, per-finding detail (explanation + citation + fix), overall summary.
- Demo: full user-facing flow, paste URL → see report in browser.

## Phase 7 — Polish & Demo Prep
- Test on 3-5 real public repos of varying size/quality to catch edge cases.
- Add a dependency-risk visualization if time allows (stretch goal from Architecture.md).
- Write the README with setup instructions, dataset citations, and architecture summary.
- Prepare a short recorded demo / slide deck summarizing problem → architecture → results (include actual classifier metrics, not just "it works").

## Explicitly Deferred (post-v1 / stretch)
- Multi-language support
- CI/CD integration for continuous auditing
- Auto-fix / auto-PR generation
- Mobile app
