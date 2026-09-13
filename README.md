# Codebase Architecture & Risk Auditor 🛡️🔍

An automated, hybrid AI-assisted code review system that combines **Deep Learning (CodeBERT)**, **Local Vector RAG (FAISS)**, **Stateful Agentic Workflows (LangGraph)**, and **Interactive Call-Graph Dependency Visualization (NetworkX + React Flow)** to scan repositories, detect line-level security vulnerabilities, provide grounded CWE/OWASP evidence, and synthesize side-by-side refactoring code fixes.

## 🚀 Key Features
- **Multi-Language AST Parsing:** Extract function boundaries and line coordinates (`filename.py:L42-L58`) using Python `ast` and `tree-sitter`.
- **Architectural Dependency Graphing:** Generate `NetworkX` directed call graphs mapping cross-file imports and invocation pathways.
- **ML Vulnerability Classifier:** Fine-tuned `microsoft/codebert-base` on the CodeXGLUE Devign dataset for semantic risk scoring.
- **Grounded Vector RAG:** Local `FAISS` vector database + `sentence-transformers` (`all-MiniLM-L6-v2`) over indexed CWE, CVE, and OWASP standards.
- **LangGraph Agentic Orchestrator:** Stateful DAG state machine (`Ingest` → `Scan` → `RAG` → `Synthesize` → `Report`) synthesizing side-by-side patch fixes.
- **Modern Dashboard UI:** React + Vite + Tailwind CSS dashboard with Security Health Score (0–100), filterable findings, side-by-side diffs, and interactive call graph.

## 📁 Repository Structure
```
├── backend/            # FastAPI REST backend & async task runner
├── frontend/           # React + Vite + Tailwind CSS dashboard
├── ml_pipeline/        # CodeBERT training & inference pipeline
├── rag_engine/         # FAISS vector database & embedding indexer
├── agent/              # LangGraph state machine agent orchestration
├── diagrams/           # System architecture, flowchart, and DFD diagrams
└── README.md
```

## 🛠️ Tech Stack
- **Languages:** Python 3.10+, JavaScript / TypeScript, C / C++
- **ML & NLP:** PyTorch, Hugging Face Transformers (`microsoft/codebert-base`), `sentence-transformers`
- **Vector DB & RAG:** FAISS (Facebook AI Similarity Search)
- **Agent Framework:** LangGraph / LangChain
- **Graph Analysis:** NetworkX, Tree-sitter
- **Web Stack:** FastAPI, React (Vite), Tailwind CSS, React Flow

---
*Created for 7th Semester Major Project (Academic Year 2026-2027)*
