# Codebase Architecture & Risk Auditor — Team Reference Guide & AI Report Blueprint

> **7th Semester Major Project Guide**  
> *Share this document with all team members for project understanding, viva preparation, and AI report generation.*

---

## 1. Executive Summary & Project Purpose

Welcome team! This document is your complete master reference for our 7th Semester Major Project: **Codebase Architecture & Risk Auditor**. 

### 💡 One-Sentence Summary:
> **An automated, neuro-symbolic AI code review and remediation platform that ingests multi-modal code inputs (GitHub repos, ZIP files, single files, raw code), detects vulnerabilities via fine-tuned CodeBERT and polyglot syntax engines (CWE-754), grounds every finding in official MITRE CWE/OWASP databases via FAISS RAG, and generates parallelized replacement code diffs using Google Gemini 2.5 Flash orchestrated by LangGraph.**

### Why Are We Building This? (The Problem Statement)
1. **High Cost & Expertise Barrier**: Manual security reviews by security engineers are expensive and out of reach for individual developers, students, and small startups.
2. **Traditional Tools Miss Real Risks**: Standard linters (Pylint, ESLint) only check surface-level style rules. They cannot reason about security risk or architectural logic flaws.
3. **Smart & Grounded Automation**: Our system acts as an automated expert security auditor. It reads the code, uses a trained ML model to catch vulnerabilities, grounds explanations in official CWE/CVE databases, and writes exact code fixes.

---

## 2. End-to-End System Workflow (Step-by-Step)

```
[ User: GitHub URL | ZIP File | Single File | Raw Code Snippet ]
                               │
                               ▼
[ 1. Ingestion & Auto-Language Detection ] ──► Detects Python, JS, Java, C/C++, etc.
                               │
                               ▼
[ 2. AST Parser & NetworkX Call Graph ] ────► Extracts functions, line ranges (L42-L58) & topology
                               │
                               ▼
[ 3. Neural Classifier & Polyglot Syntax ] ─► CodeBERT scoring + syntax error engine (CWE-754)
                               │
                               ▼
[ 4. Local Vector RAG Engine (FAISS) ] ─────► Fetches matching MITRE CWE Top 25 & OWASP rules
                               │
                               ▼
[ 5. Parallel LangGraph Agent (Gemini) ] ───► ThreadPoolExecutor parallel diff fixes + fallback
                               │
                               ▼
[ 6. React Visual Dashboard ] ──────────────► Health Score Gauge, Findings Table, Diffs & Call Graph
```

- **Step 1: Multi-Modal Ingestion & Detection** — User selects an input tab (GitHub URL, ZIP upload, single file, or raw code). Heuristic detection identifies the language and displays a badge.
- **Step 2: AST Parsing & Call Graph** — The AST parser extracts functions and line ranges (`auth.py:L42-L58`). NetworkX constructs the directed dependency call graph.
- **Step 3: ML Risk Classification & Syntax Checks** — Fine-tuned CodeBERT model (trained on Devign dataset) scans each function for 18 CWE categories. Concurrently, polyglot syntax engines validate Python, JS, Java, and C/C++ syntax under **CWE-754**.
- **Step 4: RAG Knowledge Lookup** — For flagged functions, FAISS vector search retrieves matching official CWE/CVE/OWASP rules using `sentence-transformers` embeddings (`all-MiniLM-L6-v2`).
- **Step 5: Parallel Agent Reasoning & Fix Synthesis** — LangGraph Agent combines code snippet + ML score + CWE doc, assigns severity (Critical, High, Medium, Low), and generates side-by-side replacement code using Google Gemini 2.5 Flash with thread pool concurrency (`ThreadPoolExecutor(max_workers=5)`), caching, and deterministic fallback.
- **Step 6: Dashboard Display** — React frontend displays overall Health Score (0-100), severity findings table, side-by-side code diffs, and interactive dependency risk graph.

---

## 3. Technology Stack Breakdown

| Technology | What It Is in Simple Words | Why We Used It in This Project |
|---|---|---|
| **CodeBERT (`microsoft/codebert-base`)** | A Transformer AI model (125M params) trained on source code. | Reads code structure and accurately classifies vulnerabilities. Fits in RTX 3050 VRAM. |
| **Devign Dataset (CodeXGLUE)** | Academic benchmark dataset of real vulnerable vs clean functions. | Provides ground-truth data so our model learns real security risk patterns. |
| **FAISS (Facebook AI Similarity Search)** | Free, local vector database library created by Meta. | Stores vector embeddings of CWE/CVE security docs and performs sub-millisecond search. |
| **Sentence Transformers (`all-MiniLM-L6-v2`)** | Embedding model (~80MB) turning text into 384D vectors. | Enables semantic search so RAG searches by meaning, not just exact keywords. |
| **LangGraph** | Framework for multi-step agent workflows as a Directed Acyclic Graph (DAG). | Controls state pipeline (Ingest → Scan → RAG → Fix → Report) and streams progress to UI. |
| **Google Gemini 2.5 Flash** | High-speed multi-modal LLM API with ThreadPoolExecutor parallelization. | Synthesizes side-by-side replacement code fixes with signature caching. |
| **AST & NetworkX** | AST parses code structure; NetworkX handles mathematical graph networks. | AST pinpoints function line numbers; NetworkX maps file/function call dependencies. |
| **FastAPI** | High-performance Python REST API backend. | Asynchronous, fast, type-safe, serves model & agent endpoints. |
| **React + Vite + Tailwind** | Modern frontend web stack. | Powers dark-mode dashboard with live progress, code diffs, and risk graph. |

---

## 4. Master AI Prompt for Generating Project Reports

If any teammate needs to generate the official project report/thesis document using ChatGPT, Claude, or Gemini, copy and paste this exact prompt:

```text
SYSTEM ROLE: You are an expert Computer Science Professor and Technical Writer. Write a formal, highly detailed 7th Semester B.Tech Major Project Report for the project titled "Codebase Architecture & Risk Auditor".

PROJECT SPECIFICATIONS TO INCLUDE (DO NOT ALTER THESE TECHNICAL DETAILS):
1. Project Title: Codebase Architecture & Risk Auditor
2. Target Domain: AI in Cybersecurity / Software Engineering & Static Analysis
3. Architecture Components:
   - Ingestion Layer: Multi-modal ingestion (shallow Git clone, ZIP archive decompression, single-file upload, raw code snippets with heuristic language auto-detection for Python, JS, TS, Java, C, C++, PHP, SQL, Go), AST function parser, and NetworkX directed call graph builder.
   - Classification & Syntax Layer: Fine-tuned CodeBERT (microsoft/codebert-base, 125M parameters) trained on the CodeXGLUE (Devign) dataset + polyglot syntax validation engine (Python AST, Node.js vm.Script, delimiter balancing) mapped to CWE-754 across 18 CWE Top 25 categories.
   - RAG Retrieval Layer: FAISS vector database + sentence-transformers (all-MiniLM-L6-v2) seeded with MITRE CWE Top 25, OWASP Top 10, and NVD records.
   - Agent Orchestration & Parallel Synthesis: LangGraph StateGraph DAG orchestrator with ThreadPoolExecutor(max_workers=5) driving Google Gemini 2.5 Flash for high-speed parallel replacement code diff generation, signature caching, and offline deterministic fallback.
   - Backend: FastAPI async REST API with Uvicorn.
   - Frontend: React (Vite) + Tailwind CSS + React Flow (interactive dependency risk graph) + side-by-side code diff viewer.
4. Core Features: Multi-modal ingestion, auto-language detection, polyglot syntax checking (CWE-754), 18 CWE Top 25 vulnerability scanning, exact file path & line numbers (filename.py:L42-L58), grounded CWE citations, parallel replacement code diffs, overall repository security health score (0-100).

REPORT STRUCTURE REQUIRED:
- CHAPTER 1: INTRODUCTION (Background, Problem Statement, Objectives, Scope)
- CHAPTER 2: LITERATURE SURVEY (Comparison between static linters, pure LLMs, and our Grounded RAG + ML Classifier approach)
- CHAPTER 3: SYSTEM ARCHITECTURE & DESIGN (High-level architecture diagram description, Module breakdown, Dataflow diagram description)
- CHAPTER 4: METHODOLOGY & IMPLEMENTATION (AST extraction, CodeBERT training math/loss, FAISS vector indexing, LangGraph state machine)
- CHAPTER 5: RESULTS & EXPERIMENTAL EVALUATION (Precision, Recall, F1-Score of CodeBERT on Devign, Sample scan outputs)
- CHAPTER 6: CONCLUSION & FUTURE SCOPE (Summary of findings, CI/CD integration potential)

Write the report with academic rigor, formal technical prose, equations where applicable (Cosine Similarity, Cross-Entropy Loss, F1-score formula), and clear subheadings.
```

---

## 5. Top 15 Viva Voce Questions & Answers Cheat Sheet

1. **Q: What is the main innovation of your project?**  
   *A: Combining a trained ML classifier for accurate statistical detection, a RAG pipeline for grounded CWE/CVE citations, a polyglot syntax validation engine (CWE-754), and a parallelized LangGraph agent with Gemini 2.5 Flash for rapid replacement code fix synthesis.*
2. **Q: Why use CodeBERT instead of a large LLM like GPT-4 for classification?**  
   *A: CodeBERT (125M params) is pretrained on code, fast, lightweight, runs locally within 4GB VRAM on an RTX 3050 GPU, and provides deterministic, cost-free classification.*
3. **Q: What dataset did you use to train the classifier?**  
   *A: CodeXGLUE Devign dataset containing thousands of real functions labeled as clean (0) or vulnerable (1).*
4. **Q: What is RAG and why is it necessary?**  
   *A: Retrieval-Augmented Generation searches official CWE/CVE/OWASP databases at runtime, guaranteeing every finding has a real citable source and eliminating AI hallucinations.*
5. **Q: What vector database are you using for RAG?**  
   *A: FAISS (Facebook AI Similarity Search), a 100% free, local file-based vector index.*
6. **Q: How do vector embeddings work in your setup?**  
   *A: `sentence-transformers` (`all-MiniLM-L6-v2`) converts text/code into 384D vectors, compared using Cosine Similarity.*
7. **Q: Why LangGraph over plain LangChain or CrewAI?**  
   *A: LangGraph provides an explicit Directed Acyclic Graph (DAG) state machine for step-by-step state transitions and real-time streaming to the UI.*
8. **Q: How does the system extract functions and line numbers?**  
   *A: Python native AST parser and tree-sitter parse code into structural trees, pinpointing function bounds and exact line numbers (`L42-L58`).*
9. **Q: What is the purpose of the call graph?**  
   *A: NetworkX maps how files and functions import/call each other for dependency risk visualizer in React Flow.*
10. **Q: Does your tool execute the code it audits?**  
    *A: No. It performs static analysis and parsing only, never running untrusted code.*
11. **Q: How are fix suggestions generated without timing out?**  
    *A: We utilize `ThreadPoolExecutor(max_workers=5)` for concurrent Google Gemini API requests alongside pattern signature caching, cutting audit duration from 10 minutes to ~33 seconds.*
12. **Q: How are syntax errors categorized and handled?**  
    *A: Broken syntax across Python, JavaScript, Java, and C/C++ is detected and mapped to CWE-754 (Improper Check for Unusual or Exceptional Conditions) with contextual fix suggestions.*
13. **Q: How do you handle private repositories or offline environments?**  
    *A: We support local `.zip` archive upload and raw code snippet testing, with a deterministic offline fallback synthesizer if no API key is provided.*
14. **Q: What backend framework is used?**  
    *A: FastAPI on Uvicorn (asynchronous, fast, Pydantic type-safe).*
15. **Q: What is the overall output of an audit?**  
    *A: Structured JSON Audit Report with Security Health Score (0-100), severity findings table, line-specific replacement code, grounded CWE citations, and visual dependency risk graph.*
