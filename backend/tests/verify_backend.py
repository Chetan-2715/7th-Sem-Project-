"""
backend/tests/verify_backend.py
Comprehensive standalone verification script for the Backend module.
Tests schemas, ingestion, task management, and mock reporting without external test runner.
"""

import sys
import os
import zipfile
import tempfile
import asyncio

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.schemas import (
    SeverityLevel, AuditStatus, AuditRequest, Finding,
    GraphNode, GraphEdge, DependencyGraph, AuditResult, HealthResponse
)
from backend.services.ingestor import CodebaseIngestor
from backend.services.task_manager import audit_task_manager
from backend.routers.audit import generate_sample_report
from backend.main import health_check


def test_schemas():
    print("Testing Pydantic Schemas...")
    finding = Finding(
        id="TEST-001",
        file_path="src/main.py",
        line_start=10,
        line_end=15,
        function_name="process_data",
        category="Hardcoded Secret",
        severity=SeverityLevel.HIGH,
        confidence=0.88,
        cwe_id="CWE-798",
        cwe_title="Use of Hard-coded Credentials",
        description="API key found hardcoded",
        vulnerable_code="API_KEY = 'secret'",
        fix_code="API_KEY = os.getenv('API_KEY')"
    )
    assert finding.severity == SeverityLevel.HIGH
    assert finding.confidence == 0.88

    node = GraphNode(id="main.py", label="main.py", file_path="src/main.py", risk_score=0.88)
    edge = GraphEdge(source="main.py", target="auth.py", call_type="call")
    graph = DependencyGraph(nodes=[node], edges=[edge])
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 1
    print("[OK] Pydantic Schemas verified successfully!")


def test_sample_report_generation():
    print("Testing Sample Report Generation...")
    report = generate_sample_report(repo_name="test-repo")
    assert isinstance(report, AuditResult)
    assert report.health_score == 68
    assert len(report.findings) == 4
    assert len(report.dependency_graph.nodes) > 0
    assert report.status == AuditStatus.COMPLETED
    print(f"[OK] Sample report generated successfully with {len(report.findings)} findings and health score {report.health_score}!")


def test_task_manager():
    print("Testing Async Task Manager...")
    task_id = audit_task_manager.create_task("Starting test task")
    assert task_id is not None

    status_resp = audit_task_manager.get_task(task_id)
    assert status_resp.status == AuditStatus.PENDING
    assert status_resp.progress == 0

    audit_task_manager.update_progress(task_id, 50, "Parsing AST", "Halfway through")
    status_resp = audit_task_manager.get_task(task_id)
    assert status_resp.status == AuditStatus.IN_PROGRESS
    assert status_resp.progress == 50

    sample_res = generate_sample_report("test-repo")
    audit_task_manager.complete_task(task_id, sample_res)
    status_resp = audit_task_manager.get_task(task_id)
    assert status_resp.status == AuditStatus.COMPLETED
    assert status_resp.progress == 100
    assert status_resp.result.health_score == 68
    print("[OK] Task manager progress tracking verified successfully!")


def test_ingestor_zip_safe_extract():
    print("Testing Codebase Ingestor...")
    ingestor = CodebaseIngestor()
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
        zip_path = temp_zip.name

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test_repo/sample.py", "def compute():\n    return 42\n")
            zf.writestr("test_repo/module.c", "int main() { return 0; }\n")

        extracted_dir, name = ingestor.extract_zip(zip_path)
        assert os.path.exists(extracted_dir)

        files = ingestor.walk_codebase(extracted_dir)
        assert len(files) == 2
        languages = {f["language"] for f in files}
        assert "python" in languages
        assert "c" in languages
        print(f"[OK] Ingestor extracted and discovered {len(files)} files ({languages}) successfully!")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        ingestor.cleanup(extracted_dir)


async def test_health():
    print("Testing Health Check Endpoint...")
    resp = await health_check()
    assert isinstance(resp, HealthResponse)
    assert resp.status == "ok"
    print("[OK] Health check returned ok!")


if __name__ == "__main__":
    test_schemas()
    test_sample_report_generation()
    test_task_manager()
    test_ingestor_zip_safe_extract()
    asyncio.run(test_health())
    print("\n=======================================================")
    print("[SUCCESS] ALL BACKEND CHECKS AND UNIT TESTS PASSED (100% OK)!")
    print("=======================================================")
