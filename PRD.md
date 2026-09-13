# PRD.md — Project Requirements Document

## Project Name
Codebase Architecture & Risk Auditor

## Vision
An AI-assisted auditing system that ingests a GitHub repository and produces a structured, evidence-grounded report of security vulnerabilities, risky code patterns, and architectural weaknesses — with concrete, cited fix suggestions. It replaces the manual, expert-only process of a first-pass security/architecture review with an automated agentic pipeline.

## Problem Statement
Most individual developers and small teams have no access to dedicated security or architecture review. Vulnerable code patterns, poor dependency structure, and risky practices go unnoticed until they cause real incidents (breaches, outages, technical debt spirals). Existing linters catch surface-level style issues but don't reason about *risk* or ground findings in real vulnerability knowledge.

## Target Users
- **Primary**: Individual developers / small dev teams / students who want a free first-pass security & architecture review before a real audit or code review.
- **Secondary**: Evaluators/professors/judges assessing this as an academic/portfolio project — needs a clear, demonstrable, technically credible output.

## Goals
1. Detect real vulnerability/code-smell patterns using a trained classifier (not just regex/static rules).
2. Ground every finding in actual external documentation (CVE/OWASP/CWE), not LLM hallucination.
3. Present findings as a prioritized, actionable report — not a wall of raw log output.
4. Demonstrate a genuine multi-step agentic pipeline (ingest → detect → retrieve → reason → report).

## Core Features (v1 scope)
- **Repo ingestion**: accept a public GitHub repo URL, clone and parse the file tree.
- **Code parsing**: extract functions/files for analysis; build a lightweight dependency map (which files/functions import/call which).
- **Vulnerability/smell detection**: trained classifier flags risky functions/files with a confidence score and category (e.g., injection risk, hardcoded secret, weak crypto, insecure deserialization).
- **RAG-grounded explanation**: for each flagged item, retrieve the most relevant CVE/CWE/OWASP doc snippet and use it to explain *why* it's risky, with citation.
- **Agent-generated report**: agent correlates related findings, assigns severity (Low/Medium/High/Critical), pinpoints exact file paths & line numbers (`filename.py:L42-L58`), and writes a plain-English audit report with side-by-side replacement code suggestions.
- **Dashboard UI**: severity-ranked findings table, per-finding detail view (vulnerable code vs replacement code + grounded CVE citation + line range), interactive dependency risk graph visualization.

## Out of Scope (v1)
- Automated code execution (static analysis & parsing only; no running untrusted code).
- Mobile app — web dashboard only for v1.

## Success Metrics
- End-to-end demo works: paste a real public repo URL → get a structured report within a reasonable time (target: under a few minutes for a small-to-medium repo).
- Classifier achieves reasonable precision/recall on a held-out test split of the training dataset (document the actual numbers achieved — don't overclaim).
- Every finding in the report has at least one grounded citation (no un-sourced claims).
- Report is understandable by someone who is not a security expert.

## Assumptions & Constraints
- This is a solo/small-team academic final-year project — scope must stay buildable in the available timeframe.
- Public datasets only (no proprietary vulnerability data).
- Free/low-cost tooling preferred (open-source models, free-tier vector DB, etc.) unless otherwise justified.

## Key Risks
- Trained classifier quality depends heavily on chosen dataset's relevance to the actual target language/repo types — validate this early (Phase 1/2).
- RAG corpus (CVE/CWE/OWASP docs) needs cleaning/structuring before embedding — don't underestimate this step.
- Agent orchestration complexity can balloon — keep the agent's tool set small and well-defined (see Rules.md).
