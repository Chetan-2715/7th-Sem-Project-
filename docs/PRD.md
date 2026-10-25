# PRD.md — Project Requirements Document

## Project Name
**Codebase Architecture & Risk Auditor**

## Vision
An automated, neuro-symbolic AI code review and vulnerability remediation platform that ingests source code from multiple modalities (GitHub repositories, ZIP archives, individual files, and raw code snippets) and produces a structured, evidence-grounded audit report. The platform couples deep learning (CodeBERT), dense vector retrieval (FAISS RAG over MITRE CWE Top 25 & OWASP), deterministic polyglot syntax validation, and agentic orchestration (LangGraph) with accelerated generative AI (Google Gemini 2.5 Flash) to pinpoint vulnerabilities and synthesize production-ready replacement code diffs.

---

## Problem Statement
Individual developers, academic researchers, and engineering startups rarely have access to dedicated application security engineers. As a result, critical security vulnerabilities, architectural smells, and unhandled syntax anomalies escape into production. Traditional Static Application Security Testing (SAST) linters rely on brittle regex patterns that trigger high false-positive rates and fail to understand semantic intent. Conversely, raw LLMs hallucinate non-existent CVEs and lack strict grounding. 

**Codebase Architecture & Risk Auditor** bridges this gap by providing an end-to-end, multi-agent automated security pipeline with verifiable citations and production-ready diff patches.

---

## Target Users
- **Primary**: Software developers, DevOps engineers, and students needing an instant, expert-level security and architecture audit before deployment or pull request merge.
- **Secondary**: Academic evaluators, university professors, and project review panels assessing technical rigor, neuro-symbolic integration, and verifiable RAG accuracy.

---

## Core System Goals
1. **Multi-Modal Ingestion**: Accept GitHub repository URLs, compressed ZIP archives, individual source files, and raw code snippets with automatic language detection.
2. **Semantic Defect Classification**: Detect critical security defects using a fine-tuned CodeBERT model (125M parameters) alongside 18 rule-grounded vulnerability evaluators.
3. **Polyglot Syntax Validation**: Detect broken grammar, missing tokens, and compilation errors across Python, JavaScript, TypeScript, Java, and C/C++, categorizing them under **CWE-754**.
4. **Verifiable RAG Grounding**: Ground 100% of detected vulnerabilities in an offline indexed vector database of official MITRE CWE Top 25 and OWASP standards using FAISS and `sentence-transformers`.
5. **High-Speed Parallel Patch Synthesis**: Generate side-by-side replacement code fixes using Google Gemini 2.5 Flash with thread pool concurrency and signature deduplication, dropping audit runtimes from ~10 minutes to ~30 seconds.
6. **Actionable Dashboard UI**: Present findings via a security health score dial (0–100), filterable risk tables, side-by-side diff viewers, and an interactive NetworkX dependency call graph.

---

## Core Features Breakdown

### 1. Multi-Modal Ingestion & Auto-Detection
- **GitHub Shallow Clone**: Clones public repositories with `--depth 1` for rapid analysis.
- **ZIP File Decompression**: Safely unpacks archives with path traversal (`../`) guards.
- **Single File Upload**: Instant single-file audit for rapid developer checks.
- **Raw Code Snippet**: Ingests direct code with real-time heuristic language detection across 8+ programming languages (Python, JavaScript, TypeScript, Java, C, C++, HTML/PHP, SQL, Go, Rust).

### 2. Neuro-Symbolic Vulnerability Detection (18 CWE Top 25 & OWASP)
Detects critical security weaknesses across:
- **CWE-89**: SQL Injection
- **CWE-79**: Cross-Site Scripting (Reflected, Stored, and DOM XSS)
- **CWE-78**: OS Command Injection
- **CWE-798**: Hardcoded Credentials & Secrets
- **CWE-22**: Path Traversal / Arbitrary File Read
- **CWE-502**: Deserialization of Untrusted Data (pickle, yaml, serialize)
- **CWE-94**: Code Injection (`eval`, `exec`, `Function`)
- **CWE-918**: Server-Side Request Forgery (SSRF)
- **CWE-434**: Unrestricted Upload of Dangerous File Types
- **CWE-787**: Out-of-bounds Write / Buffer Overflow
- **CWE-327**: Use of Broken or Risky Cryptographic Algorithms (MD5, SHA1, DES)
- **CWE-287**: Improper Authentication
- **CWE-862**: Missing Authorization
- **CWE-352**: Cross-Site Request Forgery (CSRF)
- **CWE-776**: XML External Entity (XXE) Injection
- **CWE-754**: Improper Check for Unusual or Exceptional Conditions (Polyglot Syntax Errors)
- Architectural smells: circular imports, untracked high blast-radius nodes, dead code.

### 3. Polyglot Syntax Error Engine (CWE-754)
- **Python**: AST compilation via `ast.parse` capturing `SyntaxError`, `IndentationError`, and non-printable characters.
- **JavaScript / TypeScript**: Evaluated using Node.js `vm.Script` syntax inspection.
- **Java / C / C++**: Delimiter balancing (braces, parentheses, brackets) and missing semicolon heuristics on imperative statements.
- **Sanitization**: Handles UTF-8 Byte Order Marks (BOM `\ufeff`) seamlessly without spurious errors. Comment lines (`#`, `//`, `/*`, `*`) are shielded from naive syntax mutations.

### 4. Dense Vector Retrieval (FAISS RAG)
- Pre-indexed vector store (`rag_engine/vector_store.py`) containing the official MITRE CWE Top 25 and OWASP security corpus.
- Sub-millisecond similarity search using `sentence-transformers` (`all-MiniLM-L6-v2`) embeddings.
- Every finding includes direct citations, official descriptions, and authoritative remediation guidelines.

### 5. Parallelized Remediation Synthesis (Google Gemini 2.5 Flash)
- Integrated via `agent/nodes.py` and `agent/llm_engine.py` using `GEMINI_API_KEY`.
- Orchestrated with `concurrent.futures.ThreadPoolExecutor(max_workers=5)` for parallel patch generation.
- Pattern-based signature caching eliminates duplicate API calls for identical vulnerability signatures.
- Local fallback synthesizer guarantees zero-downtime report generation in air-gapped or quota-exhausted environments.

### 6. Interactive Developer Dashboard
- Dark-mode developer aesthetic (`#0D1117`).
- Security Health Score Gauge (0–100) calculated from weighted severity counts:
  $$\text{Score} = \max\left(0, 100 - (25 \times \text{Critical} + 15 \times \text{High} + 8 \times \text{Medium} + 3 \times \text{Low})\right)$$
- Filterable findings table with severity badges (Critical, High, Medium, Low).
- Side-by-side Diff Viewer showing original vulnerable code against AI-generated replacement fixes.
- Interactive dependency call graph powered by React Flow and NetworkX.

---

## Out of Scope
- Dynamic execution / sandbox running of untrusted code (analysis is strictly static and neuro-symbolic).
- Native mobile applications (optimized for desktop / modern web browsers).
- Automated git pushing or direct PR merging without human developer approval.

---

## Success Metrics
- **Analysis Speed**: Small-to-medium repositories and code snippets audited in under 35 seconds (down from 10+ minutes).
- **Classification Performance**: Fine-tuned CodeBERT achieves >85% accuracy and F1 score on the CodeXGLUE Devign benchmark.
- **Zero Hallucination**: 100% of reported vulnerabilities cite verified CWE/OWASP knowledge base documents.
- **Polyglot Coverage**: Supports Python, JavaScript, TypeScript, Java, and C/C++ seamlessly.
