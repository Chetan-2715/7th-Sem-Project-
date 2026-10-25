"""
backend/schemas.py
Pydantic Data Contracts for Codebase Architecture & Risk Auditor.
Single source of truth across Backend, Parser Engine, and Frontend UI.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AuditStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# --- Request Schemas ---

class AuditRequest(BaseModel):
    """Payload to initiate an audit via GitHub URL or Raw Code."""
    repo_url: Optional[str] = Field(None, description="Public GitHub repository URL")
    branch: Optional[str] = Field("main", description="Target branch to clone (default: main)")
    raw_code: Optional[str] = Field(None, description="Raw source code string to audit")
    filename: Optional[str] = Field("snippet.py", description="Filename for raw code snippet")
    enable_rag: Optional[bool] = Field(True, description="Enable FAISS RAG grounding")
    enable_ml: Optional[bool] = Field(True, description="Enable CodeBERT classification")


# --- Graph Schemas (For AST Parser & React Flow) ---

class GraphNode(BaseModel):
    """A node representing a file or function in the dependency call-graph."""
    id: str = Field(..., description="Unique node identifier, e.g., 'auth.py:login'")
    label: str = Field(..., description="Display label in the UI")
    type: str = Field("function", description="Node type: 'file', 'function', or 'module'")
    file_path: str = Field(..., description="Relative file path in repository")
    risk_score: float = Field(0.0, description="Predicted risk score between 0.0 and 1.0")
    severity: Optional[SeverityLevel] = Field(None, description="Assigned severity if vulnerable")


class GraphEdge(BaseModel):
    """A directed edge representing a call or import dependency between two nodes."""
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    call_type: str = Field("call", description="'call' or 'import'")


class DependencyGraph(BaseModel):
    """Complete exported dependency graph compatible with React Flow."""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


# --- Finding & Vulnerability Schemas ---

class Finding(BaseModel):
    """A discrete vulnerability or architectural smell finding."""
    id: str = Field(..., description="Unique finding ID, e.g., 'FIND-001'")
    file_path: str = Field(..., description="Relative file path, e.g., 'app/routes/auth.py'")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")
    function_name: Optional[str] = Field(None, description="Enclosing function name")
    category: str = Field(..., description="Vulnerability category, e.g., 'SQL Injection'")
    severity: SeverityLevel = Field(..., description="Severity rating")
    confidence: float = Field(..., description="Model confidence score (0.0 to 1.0)")
    cwe_id: str = Field(..., description="Common Weakness Enumeration ID, e.g., 'CWE-89'")
    cwe_title: str = Field(..., description="Official title of the CWE")
    description: str = Field(..., description="Human-readable explanation of why this code is risky")
    vulnerable_code: str = Field(..., description="Original extracted vulnerable code snippet")
    fix_code: str = Field(..., description="Recommended safe replacement code snippet")
    explanation: Optional[str] = Field(None, description="Detailed grounded RAG rationale")


# --- Result & Status Schemas ---

class AuditSummary(BaseModel):
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_findings: int = 0


class AuditResult(BaseModel):
    """Final comprehensive audit report for the repository."""
    audit_id: str = Field(..., description="Unique audit UUID")
    repo_name: str = Field(..., description="Name or identifier of audited repository")
    status: AuditStatus = Field(AuditStatus.COMPLETED, description="Status of the audit")
    health_score: int = Field(..., ge=0, le=100, description="Overall codebase security score (0-100)")
    total_files: int = Field(0, description="Number of source files scanned")
    total_functions: int = Field(0, description="Total functions parsed")
    scanned_at: str = Field(..., description="ISO 8601 timestamp of audit completion")
    summary: AuditSummary = Field(default_factory=AuditSummary)
    findings: List[Finding] = Field(default_factory=list)
    dependency_graph: DependencyGraph = Field(default_factory=DependencyGraph)


class TaskStatusResponse(BaseModel):
    """Real-time polling response for background audit tasks."""
    task_id: str = Field(..., description="Audit task UUID")
    status: AuditStatus = Field(..., description="Current status of the task")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage (0-100)")
    current_stage: str = Field(..., description="e.g., 'Ingesting repository', 'Parsing AST', 'Scanning with CodeBERT'")
    message: Optional[str] = Field(None, description="Informational message or error description")
    result: Optional[AuditResult] = Field(None, description="Populated when task is COMPLETED")


class HealthResponse(BaseModel):
    """Health check response for FastAPI server."""
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "Codebase Architecture & Risk Auditor API"
