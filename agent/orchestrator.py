"""
agent/orchestrator.py
LangGraph Orchestrator for Codebase Architecture & Risk Auditor.
Coordinates the deterministic multi-step state graph:
Ingest -> Parse AST -> Scan Vulnerabilities -> RAG Grounding -> Synthesize Fixes -> Compile Report.
"""

from typing import Dict, Any, List, Optional, Callable
from backend.schemas import AuditResult
from agent.state import AuditAgentState
from agent.nodes import (
    parse_ast_node, scan_vulnerabilities_node,
    rag_grounding_node, synthesize_fixes_node, compile_report_node
)


class AuditAgentOrchestrator:
    """Manages execution of the multi-step audit agent DAG."""

    def __init__(self):
        self._has_langgraph = False
        self._compiled_graph = None
        self._init_graph()

    def _init_graph(self):
        """Attempts to compile using LangGraph StateGraph, with resilient fallback."""
        try:
            from langgraph.graph import StateGraph, END
            workflow = StateGraph(AuditAgentState)

            # Register Nodes
            workflow.add_node("parse_ast", parse_ast_node)
            workflow.add_node("scan_vulnerabilities", scan_vulnerabilities_node)
            workflow.add_node("rag_grounding", rag_grounding_node)
            workflow.add_node("synthesize_fixes", synthesize_fixes_node)
            workflow.add_node("compile_report", compile_report_node)

            # Build Edges
            workflow.set_entry_point("parse_ast")
            workflow.add_edge("parse_ast", "scan_vulnerabilities")
            workflow.add_edge("scan_vulnerabilities", "rag_grounding")
            workflow.add_edge("rag_grounding", "synthesize_fixes")
            workflow.add_edge("synthesize_fixes", "compile_report")
            workflow.add_edge("compile_report", END)

            self._compiled_graph = workflow.compile()
            self._has_langgraph = True
        except Exception:
            # Fallback deterministic DAG runner
            self._has_langgraph = False

    def run(
        self,
        repo_name: str,
        raw_files: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, str, str], None]] = None,
        enable_rag: bool = True,
        enable_ml: bool = True,
        is_raw_code: bool = False
    ) -> AuditResult:
        """
        Executes the agent workflow sequentially over ingested files.
        Optionally reports real-time progress callbacks for API polling.
        """
        initial_state: AuditAgentState = {
            "repo_name": repo_name,
            "raw_files": raw_files,
            "function_chunks": [],
            "scanned_vulnerabilities": [],
            "grounded_evidence": [],
            "grounded_findings": [],
            "enable_rag": enable_rag,
            "enable_ml": enable_ml,
            "is_raw_code": is_raw_code,
            "errors": []
        }

        if self._has_langgraph and self._compiled_graph:
            # Execute compiled LangGraph
            if progress_callback:
                progress_callback(30, "Parsing AST", "Extracting syntax trees and function boundaries...")
            final_state = self._compiled_graph.invoke(initial_state)
            return final_state["audit_result"]
        else:
            # Deterministic linear DAG execution
            state = dict(initial_state)

            # Step 1: Parse AST
            if progress_callback:
                progress_callback(35, "Parsing AST", f"Extracting function boundaries across {len(raw_files)} files...")
            ast_res = parse_ast_node(state)
            state.update(ast_res)

            # Step 2: Scan Vulnerabilities
            if progress_callback:
                progress_callback(60, "Scanning with CodeBERT", f"Analyzing {len(state.get('function_chunks', []))} functions...")
            scan_res = scan_vulnerabilities_node(state)
            state.update(scan_res)

            # Step 3: RAG Grounding
            if progress_callback:
                progress_callback(80, "FAISS RAG Retrieval", "Grounding identified patterns in official CWE/OWASP standards...")
            rag_res = rag_grounding_node(state)
            state.update(rag_res)

            # Step 4: Synthesize Fixes
            if progress_callback:
                progress_callback(90, "Synthesizing Fixes", "Generating side-by-side replacement code diffs...")
            synth_res = synthesize_fixes_node(state)
            state.update(synth_res)

            # Step 5: Compile Report
            if progress_callback:
                progress_callback(95, "Compiling Report", "Calculating Security Health Score and assembling report...")
            report_res = compile_report_node(state)
            state.update(report_res)

            return state["audit_result"]


# Global orchestrator instance
audit_orchestrator = AuditAgentOrchestrator()
