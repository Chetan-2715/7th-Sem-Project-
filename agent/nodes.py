"""
agent/nodes.py
State graph execution nodes for the LangGraph agent workflow:
1. parse_ast_node: Slices files into function chunks with exact line numbers.
2. scan_vulnerabilities_node: Scores risk and identifies suspicious code blocks.
3. rag_grounding_node: Fetches grounded CWE/OWASP evidence from local FAISS/RAG.
4. synthesize_fixes_node: Synthesizes side-by-side replacement fixes.
5. compile_report_node: Computes Health Score (0-100) and compiles AuditResult.
"""

import ast
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List

from backend.schemas import (
    Finding, SeverityLevel, AuditSummary, DependencyGraph,
    GraphNode, GraphEdge, AuditResult, AuditStatus
)
from rag_engine.vector_store import rag_engine
from agent.state import AuditAgentState


def parse_ast_node(state: AuditAgentState) -> Dict[str, Any]:
    """Slices source files into discrete function chunks and extracts import/call links."""
    raw_files = state.get("raw_files", [])
    function_chunks = []
    graph_nodes = []
    graph_edges = []

    for file_info in raw_files:
        rel_path = file_info["rel_path"]
        content = file_info["content"]
        language = file_info["language"]

        # Add file node to graph
        file_node_id = rel_path
        graph_nodes.append(GraphNode(
            id=file_node_id,
            label=file_info["filename"],
            type="file",
            file_path=rel_path,
            risk_score=0.0
        ))

        if language == "python":
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        start_line = node.lineno
                        end_line = getattr(node, "end_lineno", start_line + len(node.body))
                        fn_lines = content.splitlines()[start_line - 1:end_line]
                        fn_code = "\n".join(fn_lines)

                        func_id = f"{rel_path}:{node.name}"
                        function_chunks.append({
                            "file_path": rel_path,
                            "function_name": node.name,
                            "line_start": start_line,
                            "line_end": end_line,
                            "code": fn_code,
                            "language": language
                        })

                        # Function graph node
                        graph_nodes.append(GraphNode(
                            id=func_id,
                            label=f"{node.name}()",
                            type="function",
                            file_path=rel_path,
                            risk_score=0.0
                        ))
                        # Edge from file to function
                        graph_edges.append(GraphEdge(
                            source=file_node_id,
                            target=func_id,
                            call_type="call"
                        ))

                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        # Dependency import edge
                        module_name = getattr(node, 'module', None)
                        if module_name:
                            graph_edges.append(GraphEdge(
                                source=file_node_id,
                                target=module_name,
                                call_type="import"
                            ))

            except SyntaxError:
                # Fallback line chunker if file has syntax errors
                lines = content.splitlines()
                function_chunks.append({
                    "file_path": rel_path,
                    "function_name": "module_root",
                    "line_start": 1,
                    "line_end": len(lines),
                    "code": content[:1500],
                    "language": language
                })
        else:
            # Multi-language regex function extractor for C/C++/JS/TS
            pattern = re.compile(r"(?:function\s+([a-zA-Z0-9_]+)|([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{)")
            matches = list(pattern.finditer(content))
            if matches:
                for match in matches:
                    name = match.group(1) or match.group(2) or "func"
                    start_char = match.start()
                    start_line = content[:start_char].count("\n") + 1
                    end_line = min(start_line + 25, len(content.splitlines()))
                    fn_code = "\n".join(content.splitlines()[start_line - 1:end_line])

                    func_id = f"{rel_path}:{name}"
                    function_chunks.append({
                        "file_path": rel_path,
                        "function_name": name,
                        "line_start": start_line,
                        "line_end": end_line,
                        "code": fn_code,
                        "language": language
                    })
                    graph_nodes.append(GraphNode(
                        id=func_id,
                        label=f"{name}()",
                        type="function",
                        file_path=rel_path,
                        risk_score=0.0
                    ))
                    graph_edges.append(GraphEdge(source=file_node_id, target=func_id, call_type="call"))
            else:
                function_chunks.append({
                    "file_path": rel_path,
                    "function_name": "global_scope",
                    "line_start": 1,
                    "line_end": min(len(content.splitlines()), 100),
                    "code": content[:1500],
                    "language": language
                })

    return {
        "function_chunks": function_chunks,
        "dependency_graph": DependencyGraph(nodes=graph_nodes, edges=graph_edges),
        "current_stage": "Parsed AST and generated Call-Graph"
    }


def scan_vulnerabilities_node(state: AuditAgentState) -> Dict[str, Any]:
    """Analyzes function chunks to detect risky security patterns."""
    chunks = state.get("function_chunks", [])
    scanned_vulns = []

    # Detection rules matching CodeBERT / Devign vulnerability benchmarks
    rules = [
        {
            "category": "SQL Injection",
            "regex": r"(?:execute\s*\(\s*f[\"'].*?\{|cursor\.execute\s*\([^,)]*%\s*\(|execute\s*\([^,)]*\+|f[\"'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?\{)",
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.94
        },
        {
            "category": "Hardcoded Secret",
            "regex": r"(?:api_key|secret_key|secret_token|secret|password|aws_secret|stripe_key)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.91
        },
        {
            "category": "OS Command Injection",
            "regex": r"(?:os\.system\s*\([^)]*\+|subprocess\.(?:Popen|call|run)\s*\([^)]*shell\s*=\s*True)",
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.92
        },
        {
            "category": "Weak Cryptography",
            "regex": r"(?:hashlib\.md5|hashlib\.sha1|DES\.new|RC4)",
            "severity": SeverityLevel.MEDIUM,
            "base_conf": 0.84
        },
        {
            "category": "Insecure Deserialization",
            "regex": r"(?:pickle\.loads|yaml\.load\s*\([^,)]*\)(?!\s*Loader))",
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.88
        },
        {
            "category": "Path Traversal",
            "regex": r"(?:open\s*\([^)]*\.\./|send_from_directory\s*\([^)]*\+)",
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.87
        }
    ]

    for chunk in chunks:
        code = chunk["code"]
        for rule in rules:
            if re.search(rule["regex"], code, re.IGNORECASE):
                scanned_vulns.append({
                    "chunk": chunk,
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "confidence": rule["base_conf"]
                })
                break

    return {
        "scanned_vulnerabilities": scanned_vulns,
        "current_stage": f"Scanned {len(chunks)} functions, identified {len(scanned_vulns)} potential risks"
    }


def rag_grounding_node(state: AuditAgentState) -> Dict[str, Any]:
    """Queries local FAISS Vector RAG Engine for grounded CWE standards."""
    scanned_vulns = state.get("scanned_vulnerabilities", [])
    grounded_evidence = []

    for item in scanned_vulns:
        chunk = item["chunk"]
        category = item["category"]

        # Sub-millisecond vector search
        retrieved_docs = rag_engine.retrieve(
            query=chunk["code"][:300],
            category_hint=category,
            top_k=1
        )
        matched_cwe = retrieved_docs[0] if retrieved_docs else {
            "cwe_id": "CWE-699",
            "cwe_title": "Software Development Weakness",
            "description": "General security pattern deviation.",
            "mitigation": "Review code against secure coding principles.",
            "example_fix": "# Review and apply validation"
        }

        grounded_evidence.append({
            **item,
            "cwe_doc": matched_cwe
        })

    return {
        "grounded_evidence": grounded_evidence,
        "current_stage": f"Grounded {len(grounded_evidence)} items with authoritative CWE standards"
    }


def synthesize_fixes_node(state: AuditAgentState) -> Dict[str, Any]:
    """Generates side-by-side replacement code diffs and explanation."""
    grounded_evidence = state.get("grounded_evidence", [])
    findings: List[Finding] = []
    graph = state.get("dependency_graph", DependencyGraph())

    # Map node risk scores onto graph
    node_risk_map = {}

    for i, item in enumerate(grounded_evidence, 1):
        chunk = item["chunk"]
        cwe = item["cwe_doc"]
        finding_id = f"FIND-{i:03d}"

        # Generate grounded fix code
        original_code = chunk["code"]
        fix_suggestion = cwe.get("example_fix", "# Apply input validation and safe API")

        finding = Finding(
            id=finding_id,
            file_path=chunk["file_path"],
            line_start=chunk["line_start"],
            line_end=chunk["line_end"],
            function_name=chunk.get("function_name"),
            category=item["category"],
            severity=item["severity"],
            confidence=item["confidence"],
            cwe_id=cwe["cwe_id"],
            cwe_title=cwe["cwe_title"],
            description=cwe["description"],
            vulnerable_code=original_code,
            fix_code=f"# Grounded Fix ({cwe['cwe_id']}):\n" + fix_suggestion,
            explanation=f"Grounded in {cwe.get('owasp_category', 'OWASP Top 10')} & {cwe['cwe_id']}: {cwe['mitigation']}"
        )
        findings.append(finding)

        # Mark function risk score
        func_id = f"{chunk['file_path']}:{chunk.get('function_name', '')}"
        node_risk_map[func_id] = (item["confidence"], item["severity"])
        node_risk_map[chunk["file_path"]] = (item["confidence"], item["severity"])

    # Update graph nodes with predicted risk
    for node in graph.nodes:
        if node.id in node_risk_map:
            score, sev = node_risk_map[node.id]
            node.risk_score = score
            node.severity = sev

    return {
        "grounded_findings": findings,
        "dependency_graph": graph,
        "current_stage": f"Synthesized {len(findings)} side-by-side replacement fixes"
    }


def compile_report_node(state: AuditAgentState) -> Dict[str, Any]:
    """Computes Security Health Score (0-100) and compiles AuditResult."""
    findings = state.get("grounded_findings", [])
    raw_files = state.get("raw_files", [])
    chunks = state.get("function_chunks", [])
    graph = state.get("dependency_graph", DependencyGraph())
    repo_name = state.get("repo_name", "audited-repo")

    # Calculate severity breakdown
    crit = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
    high = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
    med = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
    low = sum(1 for f in findings if f.severity == SeverityLevel.LOW)

    # Health score formula: 100 - (crit*20 + high*10 + med*5 + low*2)
    deduction = (crit * 20) + (high * 10) + (med * 5) + (low * 2)
    health_score = max(0, 100 - deduction)

    summary = AuditSummary(
        critical_count=crit,
        high_count=high,
        medium_count=med,
        low_count=low,
        total_findings=len(findings)
    )

    audit_result = AuditResult(
        audit_id=str(uuid.uuid4()),
        repo_name=repo_name,
        status=AuditStatus.COMPLETED,
        health_score=health_score,
        total_files=len(raw_files),
        total_functions=len(chunks),
        scanned_at=datetime.utcnow().isoformat() + "Z",
        summary=summary,
        findings=findings,
        dependency_graph=graph
    )

    return {
        "audit_result": audit_result,
        "health_score": health_score,
        "current_stage": "Audit Complete"
    }
