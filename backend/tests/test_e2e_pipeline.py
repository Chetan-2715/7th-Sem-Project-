"""
backend/tests/test_e2e_pipeline.py
End-to-End integration test for the entire pipeline:
FastAPI router -> Ingestion -> AST Slicing -> RAG Grounding -> Fix Synthesis -> Final Report.
"""

import sys
import os
import zipfile
import tempfile
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.routers.audit import execute_background_audit
from backend.services.task_manager import audit_task_manager
from backend.schemas import AuditStatus


def test_full_pipeline_with_zip():
    print("Testing End-to-End Audit Pipeline with ZIP file...")

    # 1. Create a sample zip with a vulnerable python project
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
        zip_path = temp_zip.name

    try:
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "demo_repo/auth.py",
                "import os\n"
                "API_KEY = 'prod_secret_token_1234567890'\n"
                "def authenticate(user, pwd):\n"
                "    query = f\"SELECT * FROM users WHERE u='{user}' AND p='{pwd}'\"\n"
                "    db.execute(query)\n"
            )
            zf.writestr(
                "demo_repo/utils.py",
                "import hashlib\n"
                "def compute_hash(val):\n"
                "    return hashlib.md5(val.encode()).hexdigest()\n"
            )

        # 2. Initialize task
        task_id = audit_task_manager.create_task("Starting e2e test")

        # 3. Run background audit asynchronously
        asyncio.run(execute_background_audit(task_id, zip_temp_path=zip_path))

        # 4. Check completed status
        task = audit_task_manager.get_task(task_id)
        assert task is not None
        assert task.status == AuditStatus.COMPLETED
        assert task.progress == 100
        assert task.result is not None

        result = task.result
        print(f"[OK] Audit completed successfully for '{result.repo_name}'")
        print(f"[OK] Health Score: {result.health_score}/100")
        print(f"[OK] Findings Detected: {len(result.findings)}")
        print(f"[OK] Graph Nodes: {len(result.dependency_graph.nodes)}, Edges: {len(result.dependency_graph.edges)}")

        assert len(result.findings) >= 2
        categories = {f.category for f in result.findings}
        print(f"[OK] Detected Vulnerability Categories: {categories}")
        assert "SQL Injection" in categories or "Weak Cryptography" in categories

        print("\n[SUCCESS] END-TO-END PIPELINE AUDIT PASSED (100% OK)!")

    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)


if __name__ == "__main__":
    test_full_pipeline_with_zip()
