"""
backend/tests/test_backend.py
Unit tests verifying FastAPI endpoints, Pydantic schemas, and Ingestor.
"""

import os
import zipfile
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.ingestor import CodebaseIngestor
from backend.schemas import SeverityLevel, AuditResult

client = TestClient(app)


def test_health_check():
    """Verify /api/health returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_sample_report():
    """Verify /api/sample-report returns a valid AuditResult model."""
    response = client.get("/api/sample-report")
    assert response.status_code == 200
    data = response.json()
    assert "audit_id" in data
    assert "health_score" in data
    assert len(data["findings"]) == 4
    assert len(data["dependency_graph"]["nodes"]) > 0


def test_zip_extraction():
    """Verify safe zip extraction logic and file discovery."""
    ingestor = CodebaseIngestor()
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
        zip_path = temp_zip.name

    try:
        # Create a mock zip archive containing a python file
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test_repo/sample.py", "def hello():\n    print('test')\n")

        extracted_dir, name = ingestor.extract_zip(zip_path)
        assert os.path.exists(extracted_dir)

        files = ingestor.walk_codebase(extracted_dir)
        assert len(files) == 1
        assert files[0]["filename"] == "sample.py"
        assert files[0]["language"] == "python"

    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        ingestor.cleanup(extracted_dir)
