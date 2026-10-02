"""
agent/state.py
Defines the TypedDict state schema for LangGraph agent workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional
from backend.schemas import Finding, DependencyGraph, AuditResult


class AuditAgentState(TypedDict, total=False):
    """Global state passed across all nodes in the LangGraph DAG."""
    repo_name: str
    repo_dir: str
    raw_files: List[Dict[str, Any]]
    function_chunks: List[Dict[str, Any]]
    scanned_vulnerabilities: List[Dict[str, Any]]
    grounded_findings: List[Finding]
    dependency_graph: DependencyGraph
    health_score: int
    audit_result: Optional[AuditResult]
    current_stage: str
    errors: List[str]
