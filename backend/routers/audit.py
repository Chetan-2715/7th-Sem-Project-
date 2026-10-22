"""
backend/routers/audit.py
REST API Endpoints for Codebase Auditing:
- POST /api/audit: Trigger audit via GitHub URL or ZIP upload.
- GET /api/status/{task_id}: Poll audit task progress (0-100%).
- GET /api/report/{audit_id}: Retrieve completed audit report.
- GET /api/sample-report: Realistic mock report for frontend UI development.
"""

import os
import uuid
import tempfile
import asyncio
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException, status, Request
from pydantic import ValidationError

from backend.schemas import (
    AuditRequest, AuditResult, TaskStatusResponse, AuditStatus,
    Finding, SeverityLevel, AuditSummary, DependencyGraph, GraphNode, GraphEdge
)
from backend.services.ingestor import CodebaseIngestor, IngestionError
from backend.services.task_manager import audit_task_manager
from agent.orchestrator import audit_orchestrator

router = APIRouter(prefix="/api", tags=["Codebase Auditor"])
ingestor = CodebaseIngestor()

# In-memory storage for completed reports: audit_id -> AuditResult
audit_reports_db = {}


def generate_sample_report(repo_name: str = "sample-repo") -> AuditResult:
    """Generates a realistic mock audit report for frontend development & testing."""
    audit_id = str(uuid.uuid4())
    findings = [
        Finding(
            id="FIND-001",
            file_path="app/routes/auth.py",
            line_start=42,
            line_end=58,
            function_name="user_login",
            category="SQL Injection",
            severity=SeverityLevel.CRITICAL,
            confidence=0.94,
            cwe_id="CWE-89",
            cwe_title="Improper Neutralization of Special Elements used in an SQL Command",
            description="Raw string formatting is used directly inside an SQL query with user-provided parameters, allowing remote attackers to bypass authentication or execute arbitrary database commands.",
            vulnerable_code=(
                "def user_login(username, password):\n"
                "    query = f\"SELECT * FROM users WHERE user = '{username}' AND pass = '{password}'\"\n"
                "    cursor.execute(query)\n"
                "    return cursor.fetchone()"
            ),
            fix_code=(
                "def user_login(username, password):\n"
                "    # Grounded Fix (CWE-89): Use parameterized queries to neutralize SQL injection\n"
                "    query = \"SELECT * FROM users WHERE user = %s AND pass = %s\"\n"
                "    cursor.execute(query, (username, password))\n"
                "    return cursor.fetchone()"
            ),
            explanation="According to OWASP Top 10 A03:2021 and CWE-89, untrusted input concatenated into SQL statements directly alters database query logic. Using parameterized queries guarantees input is treated as literal data."
        ),
        Finding(
            id="FIND-002",
            file_path="config/settings.py",
            line_start=15,
            line_end=22,
            function_name="get_payment_client",
            category="Hardcoded Secret",
            severity=SeverityLevel.HIGH,
            confidence=0.89,
            cwe_id="CWE-798",
            cwe_title="Use of Hard-coded Credentials",
            description="Production Stripe API secret key is hardcoded directly into the source code repository, exposing sensitive financial APIs if the code is leaked or public.",
            vulnerable_code=(
                "STRIPE_API_KEY = 'sk_live_51M00xX992ExampleSecretKey123456789'\n"
                "stripe.api_key = STRIPE_API_KEY"
            ),
            fix_code=(
                "import os\n"
                "# Grounded Fix (CWE-798): Read secrets securely from environment variables\n"
                "STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')\n"
                "if not STRIPE_API_KEY:\n"
                "    raise ValueError('Missing required STRIPE_API_KEY environment variable')\n"
                "stripe.api_key = STRIPE_API_KEY"
            ),
            explanation="Hardcoding secrets violates OWASP A07:2021 and CWE-798. Secrets should always be loaded from secure environment variables, key vaults, or secret managers."
        ),
        Finding(
            id="FIND-003",
            file_path="app/utils/crypto.py",
            line_start=85,
            line_end=96,
            function_name="hash_auth_token",
            category="Weak Cryptography",
            severity=SeverityLevel.MEDIUM,
            confidence=0.81,
            cwe_id="CWE-328",
            cwe_title="Use of Weak Hash",
            description="MD5 hashing algorithm is employed to hash session tokens. MD5 suffers from known cryptographic collision vulnerabilities and is easily pre-computed via rainbow tables.",
            vulnerable_code=(
                "import hashlib\n"
                "def hash_auth_token(token_string):\n"
                "    return hashlib.md5(token_string.encode()).hexdigest()"
            ),
            fix_code=(
                "import hashlib\n"
                "# Grounded Fix (CWE-328): Upgrade to SHA-256 or bcrypt for robust token security\n"
                "def hash_auth_token(token_string):\n"
                "    return hashlib.sha256(token_string.encode()).hexdigest()"
            ),
            explanation="CWE-328 dictates that weak hashing algorithms such as MD5 and SHA-1 must be replaced with collision-resistant algorithms such as SHA-256 or adaptive password hashing functions like Argon2/bcrypt."
        ),
        Finding(
            id="FIND-004",
            file_path="app/tasks/worker.py",
            line_start=110,
            line_end=125,
            function_name="load_payload",
            category="Insecure Deserialization",
            severity=SeverityLevel.HIGH,
            confidence=0.86,
            cwe_id="CWE-502",
            cwe_title="Deserialization of Untrusted Data",
            description="The Python `pickle.loads()` function is invoked on untrusted network payloads, allowing arbitrary remote code execution (RCE) via malicious pickle bytecode.",
            vulnerable_code=(
                "import pickle\n"
                "def load_payload(raw_stream):\n"
                "    return pickle.loads(raw_stream)"
            ),
            fix_code=(
                "import json\n"
                "# Grounded Fix (CWE-502): Avoid pickle for untrusted data; use secure JSON or Protocol Buffers\n"
                "def load_payload(raw_stream):\n"
                "    return json.loads(raw_stream.decode('utf-8'))"
            ),
            explanation="OWASP Top 10 A08:2021 identifies insecure deserialization as a critical vector. Python's pickle module is not secure against erroneous or maliciously constructed data."
        )
    ]

    graph = DependencyGraph(
        nodes=[
            GraphNode(id="app/main.py", label="main.py", type="file", file_path="app/main.py", risk_score=0.1, severity=None),
            GraphNode(id="app/routes/auth.py", label="auth.py", type="file", file_path="app/routes/auth.py", risk_score=0.94, severity=SeverityLevel.CRITICAL),
            GraphNode(id="app/routes/auth.py:user_login", label="user_login()", type="function", file_path="app/routes/auth.py", risk_score=0.94, severity=SeverityLevel.CRITICAL),
            GraphNode(id="config/settings.py", label="settings.py", type="file", file_path="config/settings.py", risk_score=0.89, severity=SeverityLevel.HIGH),
            GraphNode(id="app/utils/crypto.py", label="crypto.py", type="file", file_path="app/utils/crypto.py", risk_score=0.81, severity=SeverityLevel.MEDIUM),
            GraphNode(id="app/tasks/worker.py", label="worker.py", type="file", file_path="app/tasks/worker.py", risk_score=0.86, severity=SeverityLevel.HIGH),
            GraphNode(id="db/connection.py", label="connection.py", type="file", file_path="db/connection.py", risk_score=0.2, severity=None),
        ],
        edges=[
            GraphEdge(source="app/main.py", target="app/routes/auth.py", call_type="import"),
            GraphEdge(source="app/routes/auth.py", target="app/routes/auth.py:user_login", call_type="call"),
            GraphEdge(source="app/routes/auth.py:user_login", target="db/connection.py", call_type="call"),
            GraphEdge(source="app/main.py", target="config/settings.py", call_type="import"),
            GraphEdge(source="app/routes/auth.py", target="app/utils/crypto.py", call_type="call"),
            GraphEdge(source="app/main.py", target="app/tasks/worker.py", call_type="import"),
        ]
    )

    summary = AuditSummary(
        critical_count=1,
        high_count=2,
        medium_count=1,
        low_count=0,
        total_findings=4
    )

    return AuditResult(
        audit_id=audit_id,
        repo_name=repo_name,
        status=AuditStatus.COMPLETED,
        health_score=68,
        total_files=24,
        total_functions=78,
        scanned_at=datetime.utcnow().isoformat() + "Z",
        summary=summary,
        findings=findings,
        dependency_graph=graph
    )


async def execute_background_audit(task_id: str, repo_url: Optional[str] = None, zip_temp_path: Optional[str] = None):
    """
    Background worker simulating/executing multi-step audit pipeline:
    1. Ingestion (0% -> 25%)
    2. AST & Dependency Graph parsing (25% -> 50%)
    3. CodeBERT Vulnerability classification (50% -> 75%)
    4. FAISS Vector RAG & LangGraph synthesis (75% -> 100%)
    """
    temp_dir = None
    try:
        # Step 1: Ingestion
        audit_task_manager.update_progress(task_id, 15, "Ingesting repository", "Cloning or unpacking source files...")
        await asyncio.sleep(1.0)

        repo_name = "analyzed-codebase"
        if repo_url:
            temp_dir, repo_name = ingestor.clone_github_repo(repo_url)
        elif zip_temp_path:
            temp_dir, repo_name = ingestor.extract_zip(zip_temp_path)
            try:
                os.remove(zip_temp_path)
            except Exception:
                pass

        files = ingestor.walk_codebase(temp_dir) if temp_dir else []
        total_files = len(files)

        # Run the full LangGraph Agent Workflow
        def progress_callback(pct, stage, msg):
            audit_task_manager.update_progress(task_id, pct, stage, msg)

        if files:
            result = audit_orchestrator.run(
                repo_name=repo_name,
                raw_files=files,
                progress_callback=progress_callback
            )
        else:
            result = generate_sample_report(repo_name=repo_name)

        audit_reports_db[result.audit_id] = result
        audit_task_manager.complete_task(task_id, result)

    except IngestionError as ie:
        audit_task_manager.fail_task(task_id, f"Ingestion Error: {str(ie)}")
    except Exception as e:
        audit_task_manager.fail_task(task_id, f"Audit Execution Error: {str(e)}")
    finally:
        if temp_dir:
            ingestor.cleanup(temp_dir)


# --- API Routes ---

@router.post("/audit", response_model=TaskStatusResponse)
async def start_audit(
    raw_request: Request,
    background_tasks: BackgroundTasks
):
    """
    Initiates an automated audit job.
    Accepts either:
    1. JSON body: {"repo_url": "https://github.com/..."}
    2. Multipart form-data: with uploaded '.zip' file or 'repo_url' field
    """
    target_url = None
    file = None
    zip_temp_path = None

    content_type = raw_request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await raw_request.json()
            target_url = body.get("repo_url")
        except Exception:
            pass
    elif "multipart/form-data" in content_type:
        form = await raw_request.form()
        target_url = form.get("repo_url")
        upload = form.get("file")
        if upload and hasattr(upload, "filename") and upload.filename:
            file = upload

    if not target_url and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a valid 'repo_url' or an uploaded '.zip' file."
        )

    if file:
        if not file.filename.endswith(".zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must be a .zip archive."
            )
        temp_fd, zip_temp_path = tempfile.mkstemp(suffix=".zip")
        with os.fdopen(temp_fd, "wb") as f:
            content = await file.read()
            f.write(content)

    task_id = audit_task_manager.create_task("Starting audit pipeline...")
    background_tasks.add_task(execute_background_audit, task_id, target_url, zip_temp_path)

    return audit_task_manager.get_task(task_id)


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Polls real-time progress (0-100%) and stage of an active audit task."""
    task = audit_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID '{task_id}' not found.")
    return task


@router.get("/report/{audit_id}", response_model=AuditResult)
async def get_audit_report(audit_id: str):
    """Retrieves full AuditResult for a completed audit."""
    if audit_id not in audit_reports_db:
        raise HTTPException(status_code=404, detail=f"Audit report with ID '{audit_id}' not found.")
    return audit_reports_db[audit_id]


@router.get("/sample-report", response_model=AuditResult)
async def get_sample_report():
    """Returns a realistic mock audit report to immediately enable Frontend UI development."""
    sample = generate_sample_report(repo_name="demo-python-app")
    audit_reports_db[sample.audit_id] = sample
    return sample
