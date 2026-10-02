"""
parser_engine/tests/test_parser.py
Verification test suite for AST function slicer and NetworkX dependency graph builder.
Asserts line boundary accuracy, metric extraction, graph serialization, and blast radius.
"""

import json
import os
import sys
import tempfile

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from parser_engine.ast_slicer import ASTSlicer, FunctionSlice
from parser_engine.graph_builder import GraphBuilder, BlastRadiusResult
from backend.schemas import DependencyGraph, GraphNode, GraphEdge


SAMPLE_PYTHON_CODE = '''def authenticate_user(username: str, token: str) -> bool:
    """Validate user credentials against token."""
    if not username or not token:
        return False
    hashed = hash_token(token)
    return db_lookup(username, hashed)


def hash_token(raw_token: str) -> str:
    """Compute cryptographic token digest."""
    return raw_token.strip().lower()


def db_lookup(user: str, token_hash: str):
    """Query database for user record."""
    if user == "admin":
        return True
    return False
'''


def test_ast_slicer_boundaries_and_metrics():
    """Verify function slicing, line ranges, signatures, docstrings, and complexity."""
    print("[1/5] Testing AST function slicer boundaries and metrics...")
    slicer = ASTSlicer()

    slices = slicer.slice_code(SAMPLE_PYTHON_CODE, file_path="auth.py")
    assert len(slices) == 3, f"Expected 3 functions, got {len(slices)}"

    # 1. authenticate_user
    fn1 = slices[0]
    assert fn1.name == "authenticate_user"
    assert fn1.line_start == 1
    assert fn1.line_end == 6
    assert fn1.line_range == "L1-L6"
    assert fn1.boundary == "auth.py:L1-L6"
    assert fn1.docstring == "Validate user credentials against token."
    assert "username: str" in fn1.signature
    assert fn1.arg_count == 2
    assert "username" in fn1.args and "token" in fn1.args
    assert fn1.lines_of_code == 6
    # Cyclomatic complexity: 1 (base) + 1 (if not username or not token: 1 if + 1 or) = 3
    assert fn1.cyclomatic_complexity >= 3, f"Expected complexity >= 3, got {fn1.cyclomatic_complexity}"
    assert "hash_token" in fn1.calls
    assert "db_lookup" in fn1.calls
    print(f"  [OK] Function '{fn1.name}' sliced accurately: {fn1.boundary} (Complexity: {fn1.cyclomatic_complexity})")

    # 2. hash_token
    fn2 = slices[1]
    assert fn2.name == "hash_token"
    assert fn2.line_start == 9
    assert fn2.line_end == 11
    assert fn2.line_range == "L9-L11"
    assert fn2.boundary == "auth.py:L9-L11"
    assert fn2.docstring == "Compute cryptographic token digest."
    assert fn2.arg_count == 1
    assert fn2.cyclomatic_complexity == 1
    print(f"  [OK] Function '{fn2.name}' sliced accurately: {fn2.boundary} (Complexity: {fn2.cyclomatic_complexity})")

    # 3. db_lookup
    fn3 = slices[2]
    assert fn3.name == "db_lookup"
    assert fn3.line_start == 14
    assert fn3.line_end == 18
    assert fn3.line_range == "L14-L18"
    assert fn3.boundary == "auth.py:L14-L18"
    assert fn3.cyclomatic_complexity == 2  # 1 base + 1 if
    print(f"  [OK] Function '{fn3.name}' sliced accurately: {fn3.boundary} (Complexity: {fn3.cyclomatic_complexity})")

    print("  [PASS] AST function slicer verified successfully.\n")


def test_ast_slicer_async_and_classes():
    """Verify async function detection and class method handling."""
    print("[2/5] Testing async functions and class methods...")
    code = '''class SecurityService:
    def __init__(self, key: str):
        self.key = key

    async def verify_signature(self, payload: str, sig: str) -> bool:
        """Asynchronously verify signature."""
        if not payload:
            return False
        return True
'''
    slicer = ASTSlicer()
    slices = slicer.slice_code(code, file_path="services/sec.py")
    assert len(slices) == 2, f"Expected 2 methods, got {len(slices)}"

    init_fn = slices[0]
    assert init_fn.name == "__init__"
    assert init_fn.class_name == "SecurityService"
    assert init_fn.node_id == "services/sec.py:SecurityService.__init__"

    async_fn = slices[1]
    assert async_fn.name == "verify_signature"
    assert async_fn.is_async is True
    assert async_fn.class_name == "SecurityService"
    assert async_fn.node_id == "services/sec.py:SecurityService.verify_signature"
    assert async_fn.line_range == "L5-L9"
    assert async_fn.boundary == "sec.py:L5-L9"
    print(f"  [OK] Async class method: {async_fn.node_id} ({async_fn.boundary})")
    print("  [PASS] Async and class slicing verified successfully.\n")


def test_graph_builder_and_json_export():
    """Verify NetworkX call-graph generation, cross-file linking, and JSON schema conformity."""
    print("[3/5] Testing NetworkX graph builder and Pydantic/JSON export...")

    raw_files = [
        {
            "rel_path": "api/routes.py",
            "filename": "routes.py",
            "language": "python",
            "content": '''from services.auth import login_handler

def handle_login_request(req):
    """API gateway login handler."""
    return login_handler(req.user, req.password)
'''
        },
        {
            "rel_path": "services/auth.py",
            "filename": "auth.py",
            "language": "python",
            "content": '''from database.db import execute_query

def login_handler(username, password):
    """Authenticate and fetch user details."""
    sql = f"SELECT * FROM users WHERE username = '{username}'"
    return execute_query(sql)
'''
        },
        {
            "rel_path": "database/db.py",
            "filename": "db.py",
            "language": "python",
            "content": '''def execute_query(query_str):
    """Raw database query executor."""
    return {"status": "ok", "query": query_str}
'''
        }
    ]

    builder = GraphBuilder()
    builder.build_from_raw_files(raw_files)

    # 1. Verify nodes
    node_ids = set(builder.graph.nodes)
    assert "api/routes.py:handle_login_request" in node_ids
    assert "services/auth.py:login_handler" in node_ids
    assert "database/db.py:execute_query" in node_ids

    # 2. Verify call edges
    call_edges = [
        (u, v) for u, v, d in builder.graph.edges(data=True)
        if d.get("relationship") == "calls"
    ]
    print(f"  [OK] Discovered call edges: {call_edges}")
    assert ("api/routes.py:handle_login_request", "services/auth.py:login_handler") in call_edges
    assert ("services/auth.py:login_handler", "database/db.py:execute_query") in call_edges

    # 3. Update risk on vulnerable node
    builder.update_node_risk("database/db.py:execute_query", risk_score=0.92, severity="Critical")
    db_node = builder.graph.nodes["database/db.py:execute_query"]
    assert db_node["risk_score"] == 0.92
    assert db_node["severity"] == "Critical"
    assert db_node["risk"] == "Critical"

    # 4. Verify JSON serialization
    json_str = builder.to_json(indent=2)
    assert json_str is not None and len(json_str) > 0
    parsed_json = json.loads(json_str)
    assert "nodes" in parsed_json and "edges" in parsed_json
    assert len(parsed_json["nodes"]) > 0
    assert len(parsed_json["edges"]) > 0

    # 5. Verify validation against backend.schemas.DependencyGraph
    dep_graph = builder.to_pydantic()
    assert isinstance(dep_graph, DependencyGraph)
    assert len(dep_graph.nodes) == len(parsed_json["nodes"])
    assert len(dep_graph.edges) == len(parsed_json["edges"])
    print(f"  [OK] Exported Pydantic graph with {len(dep_graph.nodes)} nodes and {len(dep_graph.edges)} edges")

    print("  [PASS] NetworkX graph builder and JSON export verified successfully.\n")


def test_blast_radius_calculation():
    """Verify upstream caller identification and blast radius metrics."""
    print("[4/5] Testing vulnerability blast radius analysis...")

    raw_files = [
        {
            "rel_path": "gateway.py",
            "filename": "gateway.py",
            "language": "python",
            "content": '''from core import service_a, service_b

def public_entrypoint(req):
    service_a(req)
    service_b(req)
'''
        },
        {
            "rel_path": "core.py",
            "filename": "core.py",
            "language": "python",
            "content": '''from storage import vulnerable_sink

def service_a(data):
    vulnerable_sink(data)

def service_b(data):
    vulnerable_sink(data)
'''
        },
        {
            "rel_path": "storage.py",
            "filename": "storage.py",
            "language": "python",
            "content": '''def vulnerable_sink(payload):
    # Potential SQL/Command injection sink
    return payload
'''
        }
    ]

    builder = GraphBuilder()
    builder.build_from_raw_files(raw_files)

    # Compute blast radius for the vulnerable sink
    target = "storage.py:vulnerable_sink"
    result: BlastRadiusResult = builder.calculate_blast_radius(target)

    print(f"  [OK] Target Node: {result.target_id}")
    print(f"  [OK] Affected Ancestors: {result.affected_nodes}")
    print(f"  [OK] Blast Radius Score: {result.blast_radius_score}")
    print(f"  [OK] Depth Map: {result.depth_map}")
    print(f"  [OK] Call Chains: {result.call_chains}")

    # Assertions
    assert target not in result.affected_nodes
    assert "core.py:service_a" in result.affected_nodes
    assert "core.py:service_b" in result.affected_nodes
    assert "gateway.py:public_entrypoint" in result.affected_nodes
    assert result.affected_count == 3

    # Check depth: service_a & service_b are 1 hop, gateway is 2 hops away
    assert result.depth_map["core.py:service_a"] == 1
    assert result.depth_map["core.py:service_b"] == 1
    assert result.depth_map["gateway.py:public_entrypoint"] == 2

    # Check call chains contain path from gateway to sink
    found_gateway_chain = any(
        chain[0] == "gateway.py:public_entrypoint" and chain[-1] == target
        for chain in result.call_chains
    )
    assert found_gateway_chain, "Expected a call chain from gateway to vulnerable sink"

    assert result.blast_risk_level in {"Critical", "High"}
    print("  [PASS] Blast radius calculation verified successfully.\n")


def test_directory_slicing_and_fallbacks():
    """Verify recursive directory slicing and multi-language fallback parsing."""
    print("[5/5] Testing directory slicing and multi-language fallbacks...")

    with tempfile.TemporaryDirectory() as temp_dir:
        f1_path = os.path.join(temp_dir, "calc.py")
        with open(f1_path, "w", encoding="utf-8") as f:
            f.write("def compute(x):\n    return x * 2\n")

        f2_path = os.path.join(temp_dir, "handler.js")
        with open(f2_path, "w", encoding="utf-8") as f:
            f.write("function processEvent(event) {\n    return event.id;\n}\n")

        slicer = ASTSlicer()
        dir_slices = slicer.slice_directory(temp_dir)

        assert any("calc.py" in k for k in dir_slices), "calc.py missing from slices"
        assert any("handler.js" in k for k in dir_slices), "handler.js missing from slices"

        js_key = next(k for k in dir_slices if "handler.js" in k)
        js_slices = dir_slices[js_key]
        assert len(js_slices) == 1
        assert js_slices[0].name == "processEvent"
        assert js_slices[0].line_range.startswith("L")
        print(f"  [OK] Multi-language fallback successfully parsed JS function: {js_slices[0].name}")

    print("  [PASS] Directory slicing and fallbacks verified successfully.\n")


def run_all_tests():
    print("=================================================================")
    print("      Parser Engine & Call Graph Verification Test Suite         ")
    print("=================================================================\n")

    test_ast_slicer_boundaries_and_metrics()
    test_ast_slicer_async_and_classes()
    test_graph_builder_and_json_export()
    test_blast_radius_calculation()
    test_directory_slicing_and_fallbacks()

    print("=================================================================")
    print("  [ALL PASSED] ALL 5 VERIFICATION SUITES PASSED CLEANLY (100% OK)!")
    print("=================================================================")


if __name__ == "__main__":
    run_all_tests()
    sys.exit(0)
