# A Project Synopsis (Review-1) On
# CODEBASE ARCHITECTURE & RISK AUDITOR

**Submitted by:**
1. Student Name 1 (Roll No: __________)
2. Student Name 2 (Roll No: __________)
3. Student Name 3 (Roll No: __________)
4. Student Name 4 (Roll No: __________)

**Under Guidance of:** [ Guide Name ]

*In partial fulfillment for the award of the degree of*  
**Bachelor of Technology IN Artificial Intelligence & Data Science Engineering**  
Pradnya Niketan Education Society, Pune.  
**NAGESH KARAJAGI ORCHID COLLEGE OF ENGINEERING & TECHNOLOGY, SOLAPUR.**  
Academic Year: 2026-2027

---

| Guide | DPAC Member | HOD |
| :---: | :---: | :---: |
| ___________________ | ___________________ | ___________________ |

---

## Abstract
Modern software engineering faces a critical cybersecurity challenge: individual developers and small software teams rarely have access to dedicated security review teams, leaving security vulnerabilities and architectural smells unnoticed until production incidents occur. Traditional static code analysis linters only enforce rigid formatting rules and surface-level syntax checks, failing to reason about semantic security risks. Conversely, ungrounded Large Language Models (LLMs) frequently introduce non-deterministic hallucinations and lack citable evidence. This project proposes "Codebase Architecture & Risk Auditor", an automated, hybrid AI-assisted code review system that integrates machine learning classification, Retrieval-Augmented Generation (RAG), and agentic workflow orchestration. The system ingests a public GitHub repository or uploaded ZIP file, shallow-clones the codebase, and extracts individual function blocks and line boundaries using Abstract Syntax Tree (AST) parsing alongside multi-language tree-sitter support. Simultaneously, a NetworkX dependency call graph maps cross-file import and function invocation relationships. A fine-tuned CodeBERT model (`microsoft/codebert-base`, 125M parameters), trained on the CodeXGLUE Devign vulnerability dataset, scans function chunks to predict vulnerability confidence scores across critical risk categories, including SQL Injection, Hardcoded Secrets, Command Injection, Weak Cryptography, and Insecure Deserialization. For every flagged vulnerability, a RAG pipeline utilizing FAISS vector storage and `sentence-transformers` (`all-MiniLM-L6-v2`) performs sub-millisecond semantic retrieval over an indexed corpus of official Common Weakness Enumeration (CWE), Common Vulnerabilities and Exposures (CVE), and OWASP Top 10 standards. Finally, a LangGraph Directed Acyclic Graph (DAG) agent orchestrates state transitions to assign severity ratings, synthesize exact side-by-side replacement code fixes, and output a structured Audit Report. The resulting React dashboard presents a Security Health Score (0-100), filterable findings, side-by-side code diffs, grounded CWE citations, and an interactive call-graph visualization.

*(Abstract Word Count: 258 words — Complies with the 200 to 300 words requirement)*

---

## Literature Review / Related Work

A survey of 15 papers and industrial applications was conducted across static code analysis, deep learning for defect detection, Retrieval-Augmented Generation, and agentic workflows:

| S.no | Author / Title of Paper Or Application / Application Title | Methodology | Outcomes | Scope for Work |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Feng et al. (2020)**<br>CodeBERT: A Pre-Trained Model for Programming and Natural Languages | Bimodal pre-training on source code and NL documentation using Transformer architectures. | Achieved SOTA performance on code search, code documentation, and defect detection. | Lacks built-in RAG grounding for official CVE/CWE security documentation. |
| **2** | **Zhou et al. (2019)**<br>Devign: Effective Vulnerability Identification Using Graph Neural Networks (CodeXGLUE) | Graph Neural Network (GNN) on Code Property Graphs (CPG) aggregating AST, control flow, and data flow. | High accuracy in detecting functions with security defects in C/C++ repositories. | Operates strictly at function level; does not generate concrete replacement fix code. |
| **3** | **Guo et al. (2021)**<br>GraphCodeBERT: Pre-training Code Representations with Data Flow | Transformer pre-training incorporating data-flow structure and variable tracking in code. | Improved code representation for clone detection and vulnerability classification. | High computational cost; requires GPU optimization for lightweight deployment. |
| **4** | **Li et al. (2018)**<br>VulDeePecker: A Deep Learning-Based System for Vulnerability Detection | Slices code into Code Gadgets based on API calls and trains Bi-LSTM networks. | Demonstrated superiority of deep learning over rule-based static analysis tools. | High false-positive rate on complex multi-file architectural logic. |
| **5** | **Li et al. (2021)**<br>SySeVR: A Framework for Using Deep Learning to Detect Vulnerabilities | Syntax-based and semantics-based vulnerability vector representation across C/C++ code. | Expanded defect detection coverage across multiple vulnerability categories. | Does not provide grounded citations or interactive visual dependency graphs. |
| **6** | **Fu & Tantithamthavorn (2022)**<br>LineVul: A Transformer-based Line-level Vulnerability Prediction | Fine-tuned CodeBERT model utilizing attention weights for line-level vulnerability prediction. | Pinpoints precise vulnerable lines within target functions with high localization. | Lacks agentic multi-step orchestration and automated patch generation. |
| **7** | **Lewis et al. (2020)**<br>Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Combines pre-trained parametric memory (LLM) with non-parametric dense vector retrieval (FAISS). | Eliminates hallucinations in open-domain QA by fetching grounded document evidence. | Needs adaptation for source code AST chunking and CWE security corpora. |
| **8** | **Johnson et al. (2019)**<br>Billion-scale similarity search with GPUs (FAISS) | GPU-accelerated vector indexing utilizing product quantization and inverted file structures. | Sub-millisecond similarity search across millions of high-dimensional vectors. | Requires specialized preprocessing for code snippet embeddings. |
| **9** | **Reimers & Gurevych (2019)**<br>Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks | Siamese network structure modifying BERT to derive semantically meaningful sentence vectors. | Significantly speeds up semantic similarity comparison from hours to milliseconds. | Optimized for natural language text; benefits from hybrid code-text corpus. |
| **10** | **LangChain & LangGraph Development Team (2024)**<br>Stateful Agent Workflow Orchestration | Directed Acyclic Graph (DAG) state machine for orchestrating tool-using LLM agents. | Enables deterministic multi-step state execution (Ingest → Scan → RAG → Fix). | Requires explicit state schema design to prevent infinite agent loop execution. |
| **11** | **MITRE Corporation (2024)**<br>Common Weakness Enumeration (CWE) & CVE NVD Dataset | Standardized dictionary of software weakness types and public vulnerability records. | Industry standard for classifying security defects and mitigation guidelines. | Raw text requires chunking and vector indexing for AI retrieval. |
| **12** | **OWASP Foundation (2023)**<br>OWASP Top 10 Web Application Security Risks | Consensus document detailing top critical security risks for web applications. | Essential benchmark for application security compliance. | Static text rules; benefits from automated RAG embedding integration. |
| **13** | **Tree-Sitter Parsing Library (2023)**<br>Incremental Parsing System for Programming Tools | Concrete Syntax Tree (CST) generator supporting multi-language grammar parsing. | Enables fast, robust function boundary extraction across Python, C++, JS, Java. | Requires AST-to-Graph conversion to model cross-file dependencies. |
| **14** | **NetworkX Graph Library (2023)**<br>Software for Complex Networks Analysis | Python library for creation, manipulation, and study of complex network structures. | Efficiently computes dependency call graphs and node risk propagation. | Purely mathematical; requires frontend visualizers (React Flow) for UI rendering. |
| **15** | **SonarQube & Snyk Application Security (2023)**<br>Commercial Static Analysis Software | Rule-based AST scanning and dependency vulnerability monitoring. | Widely adopted in corporate CI/CD pipelines. | High license cost; relies heavily on static regex matching rather than ML reasoning. |

---

## Research/Application Gaps and Objectives of the Proposed Project

### Identified Research & Application Gaps:
1. **Rigidity of Traditional Static Linters**: Tools like Pylint, ESLint, and SonarQube rely on hardcoded regex rules, resulting in high false-positive rates and an inability to reason about deep semantic security logic.
2. **Hallucination in Standalone LLMs**: Prompting general LLMs directly introduces hallucinations, unverified claims, and a lack of citations to official security standards.
3. **Absence of Actionable Fix Synthesis**: Models like Devign and VulDeePecker predict binary vulnerability labels but fail to generate concrete, ready-to-paste replacement code fixes.
4. **Lack of Visual Dependency Mapping**: Existing security tools analyze files in isolation without mapping cross-file call graphs and node risk propagation.

### Objectives of the Proposed Project:
1. **Multi-Language AST Parsing**: Parse repositories using Python native AST and `tree-sitter` into function blocks with exact line ranges (`filename.py:L42-L58`).
2. **Architectural Dependency Graphing**: Build a `NetworkX` directed call graph mapping imports and function invocation boundaries for interactive visual risk analysis.
3. **ML Vulnerability Classification**: Fine-tune `microsoft/codebert-base` on the CodeXGLUE Devign dataset to score function risk (0.0 to 1.0) across major security categories.
4. **Grounded RAG Retrieval**: Implement a local FAISS vector search utilizing `sentence-transformers` (`all-MiniLM-L6-v2`) over indexed CWE Top 25, CVE, and OWASP standards.
5. **Agentic Workflow & Fix Synthesis**: Build a LangGraph Directed Acyclic Graph (DAG) state machine (Ingest → Scan → RAG → Synthesize → Report) to synthesize side-by-side replacement code fixes.
6. **Interactive Visual UI Dashboard**: Develop a dark-mode React + Vite + Tailwind CSS dashboard presenting a Security Health Score (0-100), filterable findings, side-by-side code diffs, grounded CWE citations, and an interactive call-graph visualizer.

---

## Proposed Methodology

### System Architecture Overview
The Codebase Architecture & Risk Auditor system integrates a multi-layer pipeline combining static analysis, deep learning classification, vector RAG retrieval, and agentic orchestration:

![Figure 1: High-Level System Architecture Diagram](diagrams/architecture_diagram.png)  
*Figure 1: High-Level System Architecture Diagram*

### Detailed Module Breakdown:
1. **Module 1: Multi-Modal Ingestion & AST Call Graph**: Ingests source code via public GitHub repository URLs, uploaded ZIP archives, single files, or raw code snippets with automatic multi-language detection (Python, JS, Java, C/C++). AST and heuristic parsers extract function blocks and line boundaries (`L42-L58`), while NetworkX constructs an inter-module dependency call graph.
2. **Module 2: CodeBERT & Polyglot Syntax Evaluation**: A fine-tuned `microsoft/codebert-base` model evaluates code token sequences, while a polyglot syntax validation engine catches syntax and compilation defects across Python, JavaScript, Java, and C/C++, categorizing them under **CWE-754**.
3. **Module 3: FAISS RAG Retrieval Engine**: Converts flagged code into 384D vector embeddings and performs sub-millisecond similarity search over a local FAISS index containing official MITRE CWE Top 25 and OWASP security documentation.
4. **Module 4: Parallel LangGraph Agent Orchestrator**: LangGraph StateGraph DAG controls deterministic transitions (`Ingest` ──► `Scan` ──► `Retrieve` ──► `Synthesize` ──► `Report`), computes repository Security Health Scores, and utilizes concurrent thread pools (`ThreadPoolExecutor`) with Google Gemini 2.5 Flash to synthesize production-ready replacement code diffs in parallel.
5. **Module 5: FastAPI Backend & React Dashboard**: An asynchronous FastAPI REST backend powers the API layer, while a dark-mode React + Vite + Tailwind CSS dashboard renders the health score gauge, filterable findings table, side-by-side diff viewers, and interactive React Flow call graphs.

### Dataflow & Workflow Diagrams:

![Figure 2: Data Flow Diagram (DFD Level-1)](diagrams/data_flow_diagram.png)  
*Figure 2: Data Flow Diagram (DFD Level-1)*

![Figure 3: LangGraph Agent StateGraph DAG Workflow](diagrams/langgraph_workflow_diagram.png)  
*Figure 3: LangGraph Agent StateGraph DAG Workflow*

---

## Expected Outcomes

1. **Quantitative ML Metrics**: A fine-tuned CodeBERT model achieving high Precision, Recall, and F1-Score on the held-out Devign test split.
2. **Grounded Security Evidence**: 100% of flagged vulnerabilities accompanied by official citable CWE/CVE documentation fetched from FAISS.
3. **Side-by-Side Replacement Fixes**: Clear, line-specific code diffs showing original vulnerable code alongside ready-to-paste replacement code.
4. **Interactive Dependency Risk Graph**: Interactive React Flow call graph highlighting high-risk nodes and call propagation pathways.
5. **Working Full-Stack Application**: Production-ready FastAPI + React web application ready for live demonstration.

---

## References

1. Z. Feng et al., "CodeBERT: A Pre-Trained Model for Programming and Natural Languages," in *Proc. EMNLP Findings*, 2020, pp. 1536–1547.
2. Y. Zhou et al., "Devign: Effective Vulnerability Identification Using Graph Neural Networks," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2019, pp. 16192–16203.
3. D. Guo et al., "GraphCodeBERT: Pre-training Code Representations with Data Flow," in *Proc. ICLR*, 2021.
4. Z. Li et al., "VulDeePecker: A Deep Learning-Based System for Vulnerability Detection," in *Proc. NDSS*, 2018.
5. Z. Li et al., "SySeVR: A Framework for Using Deep Learning to Detect Vulnerabilities," *IEEE Transactions on Software Engineering*, vol. 48, no. 7, pp. 2400–2413, 2021.
6. M. Fu and C. Tantithamthavorn, "LineVul: A Transformer-based Line-level Vulnerability Prediction," in *Proc. MSR*, 2022, pp. 608–620.
7. P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2020, pp. 9459–9474.
8. J. Johnson, M. Douze, and H. Jégou, "Billion-scale similarity search with GPUs," *IEEE Transactions on Big Data*, vol. 7, no. 3, pp. 535–547, 2019.
9. N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in *Proc. EMNLP*, 2019.
10. LangChain & LangGraph Development Team, "Stateful Multi-Agent Workflow Orchestration Framework," *Documentation & Whitepaper*, 2024.
11. MITRE Corporation, "Common Weakness Enumeration (CWE) & National Vulnerability Database (NVD)," Online: https://cwe.mitre.org, 2024.
12. OWASP Foundation, "OWASP Top 10 Web Application Security Risks," Online: https://owasp.org/Top10/, 2023.
13. M. Brunsfeld et al., "Tree-Sitter: An Incremental Parsing System for Programming Tools," *GitHub Repository & Docs*, 2023.
14. A. Hagberg, D. Schult, and P. Swart, "Exploring Network Structure, Dynamics, and Function using NetworkX," in *Proc. SciPy*, 2008.
15. Snyk & SonarSource, "Static Application Security Testing (SAST) & Software Composition Analysis," *Technical Reports*, 2023.
