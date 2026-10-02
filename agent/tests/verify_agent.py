"""
agent/tests/verify_agent.py
Verification test for LangGraph Agent Orchestrator.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent.orchestrator import audit_orchestrator
from backend.schemas import AuditResult, SeverityLevel


def test_agent_pipeline():
    print("Testing LangGraph Agent Pipeline...")

    # Sample vulnerable codebase
    sample_files = [
        {
            "path": "app/db.py",
            "rel_path": "app/db.py",
            "filename": "db.py",
            "language": "python",
            "content": (
                "import os\n"
                "def find_user(username, password):\n"
                "    query = f\"SELECT * FROM users WHERE user = '{username}' AND pass = '{password}'\"\n"
                "    cursor.execute(query)\n"
                "    return cursor.fetchone()\n"
            ),
            "line_count": 6
        },
        {
            "path": "app/auth.py",
            "rel_path": "app/auth.py",
            "filename": "auth.py",
            "language": "python",
            "content": (
                "import hashlib\n"
                "SECRET_TOKEN = 'secret_key_1234567890_prod_token'\n"
                "def create_token(user_id):\n"
                "    return hashlib.md5(f'{user_id}_{SECRET_TOKEN}'.encode()).hexdigest()\n"
            ),
            "line_count": 5
        }
    ]

    stages_recorded = []

    def progress_tracker(pct, stage, msg):
        stages_recorded.append((pct, stage))
        print(f"[{pct}%] {stage}: {msg}")

    result = audit_orchestrator.run(
        repo_name="vulnerable-demo-app",
        raw_files=sample_files,
        progress_callback=progress_tracker
    )

    assert isinstance(result, AuditResult)
    assert result.total_files == 2
    assert result.total_functions >= 2
    assert len(result.findings) >= 2
    print(f"\n[OK] Audit finished with Health Score: {result.health_score}/100")
    print(f"[OK] Total Findings Detected: {len(result.findings)}")

    categories = [f.category for f in result.findings]
    print(f"[OK] Detected Categories: {categories}")
    assert "SQL Injection" in categories

    for f in result.findings:
        print(f" - [{f.severity.value}] {f.category} in {f.file_path}:{f.line_start}-{f.line_end} ({f.cwe_id})")
        assert f.cwe_id.startswith("CWE-")
        assert len(f.fix_code) > 0

    assert len(result.dependency_graph.nodes) > 0
    print("\n[SUCCESS] LANGGRAPH AGENT WORKFLOW PASSED (100% OK)!")


if __name__ == "__main__":
    test_agent_pipeline()
