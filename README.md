# Codebase Architecture & Risk Auditor 🛡️🔍
> **An Automated, Neuro-Symbolic Code Review & Vulnerability Remediation Platform**  
> *Combining CodeBERT Deep Learning, FAISS Local Vector RAG, LangGraph Multi-Agent Orchestration, Polyglot Syntax Evaluation, and Parallelized Generative Patch Synthesis (Google Gemini 2.5 Flash).*

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1%2Bcu121-EE4C2C.svg)](https://pytorch.org/)
[![Model](https://img.shields.io/badge/CodeBERT-125M%20Parameters-yellow.svg)](https://huggingface.co/microsoft/codebert-base)
[![RAG](https://img.shields.io/badge/Vector%20RAG-FAISS%20%2B%20MiniLM-green.svg)](https://github.com/facebookresearch/faiss)
[![Orchestrator](https://img.shields.io/badge/Agent-LangGraph%20State%20DAG-blueviolet.svg)](https://github.com/langchain-ai/langgraph)
[![GenAI](https://img.shields.io/badge/Patch%20Synthesis-Google%20Gemini%202.5%20Flash-4285F4.svg)](https://ai.google.dev/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20REST-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20Tailwind-61DAFB.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## 📚 Project Documentation Hub
All architectural specifications, designs, PRDs, team execution guides, and academic papers are neatly organized in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| 📖 [**Architecture Specification**](docs/Architecture.md) | High-level system architecture, data pipelines, LangGraph state machine, and API contracts. |
| 🎨 [**UI/UX Design Guidelines**](docs/Design.md) | Theme tokens (`#0D1117`), component hierarchy, diff viewers, and React Flow visualizers. |
| 📋 [**Product Requirements Document (PRD)**](docs/PRD.md) | Core vision, user stories, success criteria, and system scope. |
| 🗺️ [**Build Roadmap & Phases**](docs/Phases.md) | Milestone execution tracker from Phase 0 to Phase 8. |
| ⚖️ [**Rules & Engineering Boundaries**](docs/Rules.md) | Coding standards, API quota safeguards, concurrency limits, and security constraints. |
| 🧠 [**Persistent Memory & Decisions**](docs/Memory.md) | Historical log of design choices, benchmark numbers, and technical changes. |
| 🤖 [**AI Assistant & Contributor Guide**](docs/instructions.md) | Guidelines for contributors, setup instructions, and testing protocols. |
| 🎓 [**Academic Project Synopsis**](docs/Project_Synopsis_Review_1_Official.md) | Official Review-1 synopsis for university thesis submission. |
| 👥 [**Team Viva & Report Prompt**](docs/TEAM_GUIDE_AND_REPORT_PROMPT.md) | Comprehensive viva voce cheat sheet and master LLM prompt for generating thesis reports. |

---

## 📑 Table of Contents
1. [Executive Summary & Motivation](#-executive-summary--motivation)
2. [Key Innovations & New Capabilities](#-key-innovations--new-capabilities)
3. [High-Level System Architecture](#-high-level-system-architecture)
4. [Deep-Dive Module Breakdown](#-deep-dive-module-breakdown)
   - [1. Multi-Modal Ingestion & Auto-Language Detection (`backend/services/ingestor.py`)](#1-multi-modal-ingestion--auto-language-detection)
   - [2. AST Slicer & NetworkX Call Graph (`parser_engine/`)](#2-ast-slicer--networkx-call-graph)
   - [3. CodeBERT Vulnerability Classifier (`ml_pipeline/`)](#3-codebert-vulnerability-classifier)
   - [4. Polyglot Syntax Error Engine under CWE-754 (`agent/nodes.py`)](#4-polyglot-syntax-error-engine-cwe-754)
   - [5. Local Dense Vector RAG Engine (`rag_engine/`)](#5-local-dense-vector-rag-engine)
   - [6. Parallelized AI Fix Synthesizer (`agent/nodes.py`)](#6-parallelized-ai-fix-synthesizer)
   - [7. Modern React Developer Dashboard (`frontend/`)](#7-modern-react-developer-dashboard)
5. [Dataset & Model Training Benchmarks](#-dataset--model-training-benchmarks)
6. [Installation & Quickstart Guide](#-installation--quickstart-guide)
7. [REST API Documentation](#-rest-api-documentation)
8. [Project Directory Structure](#-project-directory-structure)

---

## 💡 Executive Summary & Motivation

Modern software engineering suffers from a dual crisis in application security:
1. **High Cost & False Positives of Legacy SAST**: Traditional Static Application Security Testing (SAST) tools rely heavily on rigid regex patterns and rule-based linters. This leads to high false-positive rates, an inability to understand developer intent, and zero capability to generate validated replacement code.
2. **Hallucination & Lack of Grounding in Pure LLMs**: Using raw Large Language Models for security audits introduces non-deterministic hallucinations, fabricated CVE numbers, and insecure suggestions.
3. **Architectural Opacity**: Complex codebases obscure dependency risks where a vulnerable function compromises multiple downstream components.

The **Codebase Architecture & Risk Auditor** introduces a **Neuro-Symbolic Hybrid Architecture**:
- **Symbolic Analysis (AST & Call Graphs)**: Deterministically parses code into discrete functions with line boundaries (`filename.py:L42-L58`) and maps cross-file invocations using NetworkX.
- **Deep Neural Representation (CodeBERT)**: Employs a 125M-parameter Transformer fine-tuned on the CodeXGLUE Devign dataset to score vulnerabilities beyond surface-level syntax.
- **Polyglot Syntax Engine (CWE-754)**: Detects syntax, compilation, and token errors across Python, JavaScript, Java, and C/C++, preventing broken code from escaping into production.
- **Grounded Retrieval-Augmented Generation (FAISS RAG)**: Matches every risk against an offline indexed vector store of official **MITRE CWE Top 25** and **OWASP Top 10** standards to guarantee evidence citations.
- **Parallel Generative Fix Synthesis (Google Gemini 2.5 Flash)**: Generates side-by-side replacement code diffs concurrently with `ThreadPoolExecutor(max_workers=5)` and pattern caching, reducing audit duration from 10+ minutes to ~33 seconds.

---

## 🚀 Key Innovations & New Capabilities

- 📥 **Multi-Modal Ingestion**: Audit code through 4 convenient modes:
  1. **GitHub Repository**: Instant shallow clone (`--depth 1`).
  2. **ZIP File**: Upload and decompress with Zip-Slip path traversal security.
  3. **Single File**: Fast inspection of isolated source code files.
  4. **Raw Code Snippet**: Direct paste with instant heuristic language auto-detection.
- ⚡ **Real-Time Language Auto-Detection**: Dynamically detects Python, JavaScript, TypeScript, Java, C, C++, PHP, SQL, Go, and Rust, displaying a live badge in the dashboard.
- 🛠️ **Polyglot Syntax Engine (CWE-754)**:
  - Python: AST compilation via `ast.parse` capturing indentation, syntax, and invalid token errors.
  - JavaScript / TypeScript: Node.js `vm.Script` syntax inspection.
  - Java / C / C++: Delimiter balancing (braces, parentheses, brackets) and missing semicolon detection on imperative statements.
  - Contextual fix synthesis provides immediate, compile-ready corrections.
- 🛡️ **18 MITRE CWE Top 25 & OWASP Rule Coverage**: Full evaluation across SQL Injection (CWE-89), XSS (CWE-79), Command Injection (CWE-78), Hardcoded Secrets (CWE-798), Path Traversal (CWE-22), Deserialization (CWE-502), SSRF (CWE-918), Buffer Overflow (CWE-787), Broken Crypto (CWE-327), Syntax Errors (CWE-754), and more.
- ⚡ **Parallel AI Remediation**: Concurrent thread pools (`ThreadPoolExecutor`) and in-memory pattern caching slash audit latency by **95%** (from ~10 minutes down to ~33 seconds for 50 findings).
- 🔒 **Zero-Downtime Deterministic Fallback**: If an external API key is absent or quota is exceeded, the offline deterministic fallback synthesizer immediately writes verified replacement code.
- 🔤 **UTF-8 BOM Normalization & Comment Guarding**: Strips Windows UTF-8 Byte Order Marks (`\ufeff`) seamlessly and protects code comments (`#`, `//`, `/*`, `*`) from false syntax mutations.
- 🔐 **Hardened Secrets Management**: Strict `.gitignore` policy isolates `.env` while providing `.env.example` templates.

---

## 🏛️ High-Level System Architecture

```
[ Input: GitHub Repo | ZIP Archive | Single File | Raw Code Snippet ]
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION & LANGUAGE RECOGNITION (backend/services/ingestor.py)            │
│   • Shallow Git Clone (--depth 1) or ZIP extraction with path safety          │
│   • Heuristic Language Detection (Python, JS, TS, Java, C, C++, PHP, SQL, Go)│
│   • UTF-8 BOM (\ufeff) Normalization & Multi-Line Sanitization                │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 2. PARSING & DEPENDENCY GRAPH ENGINE (parser_engine/ & agent/nodes.py)        │
│   • AST Slicing: Functions, signatures, and exact line ranges (file.py:L42-58)│
│   • NetworkX DiGraph: Cross-file module import and invocation topology        │
│   • Polyglot Syntax Engine: Python AST, Node vm.Script, delimiter balancing   │
│   • Maps broken syntax, unclosed braces, and missing semicolons to CWE-754    │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 3. NEURAL & SYMBOLIC CLASSIFIER (ml_pipeline/ & agent/nodes.py)               │
│   • Fine-Tuned CodeBERT (125M parameters) trained on CodeXGLUE Devign dataset │
│   • Evaluates 18 MITRE CWE Top 25 & OWASP vulnerability categories             │
│   • Outputs confidence scores (0.0 to 1.0) and vulnerability classifications  │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 4. DENSE VECTOR RAG RETRIEVAL (rag_engine/vector_store.py)                    │
│   • sentence-transformers (all-MiniLM-L6-v2) generates 384-d dense vectors    │
│   • Local FAISS index searches official MITRE CWE & OWASP documentation       │
│   • Sub-millisecond top-k retrieval of grounded descriptions & mitigations    │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 5. PARALLELIZED LANGGRAPH AGENT (agent/orchestrator.py & agent/nodes.py)      │
│   • StateGraph DAG: Ingest ──► Scan ──► Retrieve ──► Synthesize ──► Report    │
│   • Concurrent Fix Synthesis via ThreadPoolExecutor(max_workers=5)            │
│   • Google Gemini 2.5 Flash API with signature deduplication caching          │
│   • Offline deterministic fallback synthesizer for zero-downtime reliability  │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 6. FASTAPI ASYNC BACKEND (backend/main.py & backend/routers/audit.py)         │
│   • Background task execution with thread-safe TaskManager                    │
│   • Pydantic schema validation (AuditRequest, AuditResult, Finding)           │
│   • REST polling & real-time progress updates (0% to 100%)                    │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ 7. REACT AUDIT DASHBOARD (frontend/src/)                                      │
│   • 4 Ingestion Tabs: GitHub Repo, ZIP File, Single File, Raw Code            │
│   • Real-Time Auto-Detected Language Indicator Badge                          │
│   • Security Health Score Gauge (0–100)                                       │
│   • Filterable findings table with severity badges (Critical, High, Med, Low) │
│   • Side-by-side Monaco-style Diff Viewer highlighting replacement code       │
│   • React Flow interactive dependency call graph                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Deep-Dive Module Breakdown

### 1. Multi-Modal Ingestion & Auto-Language Detection
- **`backend/services/ingestor.py`**:
  - Implements shallow cloning (`git clone --depth 1`) to minimize network bandwidth and storage overhead.
  - Safe ZIP extraction with path traversal guards (`os.path.commonpath`) mitigating Zip-Slip vulnerabilities.
  - Single-file and raw code snippet ingestion with automated line counting and character normalization.
  - Heuristic language detection scores syntax keywords, function definitions, and package imports to instantly classify input code into Python, JavaScript, TypeScript, Java, C, C++, PHP, SQL, Go, or Rust.
  - Normalizes UTF-8 BOM prefixes (`\xef\xbb\xbf` / `\ufeff`).

### 2. AST Slicer & NetworkX Call Graph
- **`parser_engine/ast_slicer.py`**:
  - Slices codebases into discrete function units with line-level bounds (`filename.py:L42-L58`).
  - Extracts signatures, parameter counts, docstrings, and cyclomatic complexity metrics.
- **`parser_engine/graph_builder.py`**:
  - Constructs a directed graph (`networkx.DiGraph`) representing inter-file imports and invocation flows.
  - Calculates degree centrality to map the blast radius of vulnerable components.

### 3. CodeBERT Vulnerability Classifier
- **`ml_pipeline/model.py` & `ml_pipeline/inference.py`**:
  - Transformer model built on `microsoft/codebert-base` (125M parameters, 12 layers, 768 hidden dimensions).
  - Fine-tuned on the CodeXGLUE Devign dataset using PyTorch with `fp16` mixed precision.
  - Evaluates code sequences and outputs vulnerability confidence probabilities ($0.0$ to $1.0$).

### 4. Polyglot Syntax Error Engine (CWE-754)
- **`agent/nodes.py` (`check_polyglot_syntax`)**:
  - Catches syntax, compilation, and token errors across languages:
    - **Python**: Compiles AST trees via `ast.parse`.
    - **JavaScript / TypeScript**: Validates tokens with Node.js `vm.Script`.
    - **Java / C / C++**: Delimiter balancing (braces, parentheses, brackets) and missing semicolon heuristics on return and assignment statements.
  - Categorizes all syntax anomalies under **CWE-754: Improper Check for Unusual or Exceptional Conditions** with authoritative mitigations.

### 5. Local Dense Vector RAG Engine
- **`rag_engine/vector_store.py`**:
  - Local Meta FAISS index (`faiss.IndexFlatL2`) holding verified MITRE CWE Top 25 and OWASP entries.
  - 384-dimensional dense vectors generated via `sentence-transformers/all-MiniLM-L6-v2`.
  - Guarantees 100% grounded citations and official mitigation guidelines without hallucination.

### 6. Parallelized AI Fix Synthesizer
- **`agent/nodes.py` & `agent/llm_engine.py`**:
  - Utilizes Google Gemini 2.5 Flash via `google-genai` SDK.
  - Parallelized execution via `ThreadPoolExecutor(max_workers=5)` reduces 50-finding audit times from ~10 minutes to **~33 seconds**.
  - In-memory signature deduplication cache (`_fix_cache`) skips redundant API calls for duplicate vulnerability patterns.
  - Offline deterministic fallback generator ensures zero-downtime report generation in rate-limited or air-gapped environments.
  - Comment shielding prevents comment lines from being mutated into invalid code.

### 7. Modern React Developer Dashboard
- **`frontend/src/`**:
  - Dark-mode developer interface (`#0D1117`) built with React 18, Vite, and Tailwind CSS.
  - **4 Ingestion Modes**: GitHub Repo, ZIP Archive, Single File, Raw Code Snippet.
  - **Health Score Dial**: Circular SVG gauge (0–100):
    $$\text{Score} = \max\left(0, 100 - (25 \times \text{Critical} + 15 \times \text{High} + 8 \times \text{Medium} + 3 \times \text{Low})\right)$$
  - **Findings Table**: Filterable by severity and category, with expandable rows showing grounded CWE citations and agent reasoning.
  - **Diff Viewer**: Side-by-side Monaco-style code viewer with one-click copy.
  - **Dependency Call Graph**: Interactive React Flow visualizer rendering NetworkX call paths.

---

## 📊 Dataset & Model Training Benchmarks

The deep learning model was fine-tuned on the academic standard **CodeXGLUE Devign** vulnerability dataset:

| Metric | CodeBERT Performance (Devign Test Split) |
|---|---|
| **Accuracy** | **87.50%** |
| **Precision** | **85.71%** |
| **Recall** | **85.71%** |
| **F1-Score** | **0.8571** |
| **Hardware** | NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM) |
| **Mixed Precision** | PyTorch Native `fp16` Automatic Mixed Precision (AMP) |
| **Checkpoint Format** | Hugging Face SafeTensors (zero-code execution risk) |

---

## 🚀 Installation & Quickstart Guide

### Prerequisites
- **Python**: 3.10 or 3.11
- **Node.js**: v18+ and npm
- **Git**: Installed and on system PATH

### 1. Clone the Repository
```bash
git clone https://github.com/Chetan-2715/7th-Sem-Project-.git
cd 7th-Sem-Project-
```

### 2. Configure Environment Secrets
Copy the template configuration file:
```bash
cp .env.example .env
```
Open `.env` and insert your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: If no API key is provided, the platform automatically utilizes its local deterministic fallback patch generator).*

### 3. Set Up Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### 5. Launch the Servers

#### Terminal 1 — Start Backend Server (FastAPI)
```powershell
.\venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger API docs available at: `http://localhost:8000/docs`

#### Terminal 2 — Start Frontend Server (React + Vite)
```powershell
cd frontend
npm run dev -- --host
```
Open your browser at: `http://localhost:5173`

---

## 📡 REST API Documentation

| Method | Endpoint | Request Body / Form | Description |
|---|---|---|---|
| `POST` | `/api/audit` | `{"repo_url": "https://github.com/..."}` | Initiates asynchronous audit on a public GitHub repo |
| `POST` | `/api/audit-upload` | Multipart Form: `file` (ZIP) | Safely unpacks and audits uploaded ZIP archive |
| `POST` | `/api/audit-file` | Multipart Form: `file` (single file) | Audits an individual source code file |
| `POST` | `/api/audit-raw` | `{"code": "...", "language": "auto"}` | Audits raw code snippet with auto-detected language |
| `GET` | `/api/audit/{task_id}/status` | None | Returns real-time status and stage progress (`0-100%`) |
| `GET` | `/api/audit/{task_id}/report` | None | Returns the full structured `AuditResult` report |
| `GET` | `/api/health` | None | System health check and model availability status |
| `GET` | `/api/sample-report` | None | Returns a pre-computed sample report for rapid testing |

---

## 📂 Project Directory Structure

```
D:\7th SEM MAJOR\
├── .env.example                       # Environment configuration template
├── .gitignore                          # Strict gitignore protecting keys, venvs, binaries
├── README.md                           # Master repository showcase and overview
├── requirements.txt                    # Root Python dependencies
│
├── docs/                               # Comprehensive project documentation
│   ├── Architecture.md                 # System architecture and data flow
│   ├── Design.md                       # UI/UX design specifications and color tokens
│   ├── PRD.md                          # Product Requirements Document
│   ├── Phases.md                       # Build roadmap and team execution plan
│   ├── Rules.md                        # AI developer rules and development boundaries
│   ├── Memory.md                       # Persistent progress log and decisions ledger
│   ├── instructions.md                 # Guidelines for AI assistants and contributors
│   ├── Project_Synopsis_Review_1_Official.md # Academic project synopsis
│   └── TEAM_GUIDE_AND_REPORT_PROMPT.md # Team guide and AI viva prompt
│
├── agent/                              # LangGraph Agentic Pipeline
│   ├── llm_engine.py                   # Google Gemini API connector with fallback
│   ├── nodes.py                        # Execution nodes (polyglot syntax, scanner, parallel fix)
│   ├── orchestrator.py                 # LangGraph StateGraph DAG definition
│   ├── state.py                        # TypedDict AgentState schema
│   └── tests/verify_agent.py           # Unit verification test suite
│
├── backend/                            # FastAPI REST Backend
│   ├── main.py                         # Application entrypoint & CORS configuration
│   ├── schemas.py                      # Pydantic data schemas (AuditRequest, Finding, etc.)
│   ├── routers/
│   │   └── audit.py                    # Multi-modal audit endpoints (/audit, /audit-raw, etc.)
│   ├── services/
│   │   ├── ingestor.py                 # Ingestion service (Git, ZIP, file, raw code)
│   │   └── task_manager.py             # Asynchronous thread-safe task manager
│   └── tests/
│       ├── test_backend.py             # Pytest endpoint validation
│       └── test_e2e_pipeline.py        # End-to-end integration tests
│
├── frontend/                           # React + Vite Developer Dashboard
│   ├── src/
│   │   ├── App.jsx                     # Core application view & audit state machine
│   │   ├── components/
│   │   │   ├── AuditInput.jsx          # 4-mode input component with auto-language badge
│   │   │   ├── HealthScoreGauge.jsx    # SVG circular health score gauge (0-100)
│   │   │   ├── MetricCards.jsx         # Summary cards (Total, Critical, High, Medium, Low)
│   │   │   ├── FindingsTable.jsx       # Interactive findings table with search & filters
│   │   │   ├── DiffViewer.jsx          # Side-by-side original vs fixed code diff viewer
│   │   │   ├── DependencyFlow.jsx      # React Flow interactive dependency call graph
│   │   │   ├── ProgressBar.jsx         # Multi-stage animated pipeline progress indicator
│   │   │   └── Header.jsx              # Navigation header with system health status
│   │   └── index.css                   # Tailwind CSS styling and theme definitions
│   ├── package.json
│   └── vite.config.js
│
├── ml_pipeline/                        # Deep Learning Classification Engine
│   ├── model.py                        # CodeBERT sequence classification wrapper
│   ├── dataset.py                      # PyTorch Dataset for CodeXGLUE Devign
│   ├── train.py                        # Model training script with mixed-precision fp16
│   ├── inference.py                    # Standalone snippet inference tester
│   └── download_dataset.py             # Automated Devign dataset fetcher
│
├── parser_engine/                      # Symbolic Code Parsing & Graph Engine
│   ├── ast_slicer.py                   # AST function extraction with line numbers (L42-L58)
│   ├── graph_builder.py                # NetworkX call graph constructor
│   └── tests/test_parser.py            # Unit test suite for AST and Graph engines
│
└── rag_engine/                         # Retrieval-Augmented Generation Layer
    ├── vector_store.py                 # FAISS local vector store with MiniLM embeddings
    ├── corpus/
    │   └── cwe_owasp_knowledge_base.json # Curated MITRE CWE Top 25 & OWASP knowledge base
    └── tests/verify_rag.py             # RAG retrieval accuracy test suite
```

---

*Authored for the 7th Semester Major Project (Academic Year 2026–2027).*  
*Open Source under the [MIT License](LICENSE).*
