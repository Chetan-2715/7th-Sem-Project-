# Architecture.md

## High-Level Flow
```
User Input (GitHub repo URL)
        |
        v
[1] Repo Ingestion Service
    - Clone repo (shallow clone)
    - Walk file tree, filter by target language/extension
        |
        v
[2] Code Parsing & Feature Extraction
    - Split into functions/chunks
    - Build lightweight dependency map (imports/calls)
        |
        v
[3] Trained Classifier (Vulnerability/Smell Detection)
    - Run each code chunk through the model
    - Output: flagged items with category + confidence score
        |
        v
[4] RAG Retrieval Layer
    - Embed flagged item context
    - Query vector DB (CVE/CWE/OWASP corpus)
    - Return top-k relevant grounding docs per finding
        |
        v
[5] Orchestrating Agent
    - Correlate related findings across files
    - Assign severity per finding
    - Generate explanation + fix suggestion, citing retrieved docs
    - Compile final structured report (JSON)
        |
        v
[6] Backend API (FastAPI)
    - Exposes /audit endpoint, orchestrates steps 1-5
    - Returns structured JSON report
        |
        v
[7] Frontend (React)
    - Input form, progress indicator
    - Results dashboard: findings table, detail view, summary
```

## Tech Stack
| Layer | Technology |
|---|---|
| Repo ingestion | GitPython or `git clone` via subprocess |
| Code parsing | `ast` module (Python) & AST dependency graph generator |
| Trained model | Fine-tuned CodeBERT (`microsoft/codebert-base`, 125M params, fits RTX 3050 VRAM) |
| Model training/eval | PyTorch + HuggingFace `transformers` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, ~80MB RAM, zero API cost) |
| Vector DB | **FAISS** (100% free, local file-based index, zero dependencies) |
| Agent orchestration | **LangGraph** (StateGraph DAG with streaming node execution) |
| LLM (for agent reasoning/report generation) | Flexible OpenAI-compatible API (**OpenRouter**, **NVIDIA NIM**, **Groq**, or 100% offline local **Ollama** `qwen2.5-coder`) |
| Backend | FastAPI + Uvicorn |
| Frontend | React (Vite) + Tailwind CSS |
| Data storage | SQLite (job/report history) — Postgres if scaling later |

## Folder Structure
```
codebase-auditor/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── api/
│   │   │   └── audit.py           # /audit endpoint
│   │   ├── ingestion/
│   │   │   ├── clone.py
│   │   │   └── parse.py
│   │   ├── model/
│   │   │   ├── train.py           # classifier training script
│   │   │   ├── inference.py
│   │   │   └── weights/           # saved model artifacts
│   │   ├── rag/
│   │   │   ├── build_index.py     # embeds CVE/CWE/OWASP corpus
│   │   │   ├── retrieve.py
│   │   │   └── corpus/            # raw docs before embedding
│   │   ├── agent/
│   │   │   ├── orchestrator.py    # LangGraph/CrewAI pipeline
│   │   │   └── tools.py
│   │   ├── schemas/                # Pydantic models
│   │   └── db/
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/                   # backend API calls
│   │   └── App.jsx
│   ├── package.json
│   └── index.html
├── data/
│   └── datasets/                  # CodeXGLUE/Devign, CVE dumps (gitignored if large)
├── PRD.md
├── Architecture.md
├── Rules.md
├── Phases.md
├── Design.md
├── Memory.md
└── README.md
```

## Key API Endpoints (v1)
- `POST /audit` — body: `{ repo_url: string }` → starts an audit job, returns `job_id`
- `GET /audit/{job_id}/status` — poll job progress
- `GET /audit/{job_id}/report` — returns final structured JSON report

## Data Flow Notes
- Repo cloning and parsing happen synchronously per job; for v1, a single job can run as a blocking background task (no need for a full job queue unless repos are large).
- The classifier and RAG retrieval are independent steps — classifier runs first to identify *what* to look up, then RAG grounds *why* it matters.
- The agent is the only component allowed to produce natural-language report text — the classifier and retrieval layers only output structured data.
