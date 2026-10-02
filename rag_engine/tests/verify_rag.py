"""
rag_engine/tests/verify_rag.py
Verification test for local Vector RAG Engine.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from rag_engine.vector_store import rag_engine


def test_rag_retrieval():
    print("Testing Vector RAG Engine...")

    # Test 1: SQL Injection query
    results_sqli = rag_engine.retrieve(
        query="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        category_hint="SQL Injection",
        top_k=1
    )
    assert len(results_sqli) > 0
    top_sqli = results_sqli[0]
    print(f"[OK] Query 1 matched: {top_sqli['cwe_id']} - {top_sqli['cwe_title']}")
    assert top_sqli["cwe_id"] == "CWE-89"

    # Test 2: Hardcoded Secret query
    results_secret = rag_engine.retrieve(
        query="AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE'",
        category_hint="Hardcoded Secret",
        top_k=1
    )
    assert len(results_secret) > 0
    top_secret = results_secret[0]
    print(f"[OK] Query 2 matched: {top_secret['cwe_id']} - {top_secret['cwe_title']}")
    assert top_secret["cwe_id"] == "CWE-798"

    # Test 3: Weak Crypto query
    results_crypto = rag_engine.retrieve(
        query="hashlib.md5(token.encode()).hexdigest()",
        category_hint="Weak Hash",
        top_k=1
    )
    assert len(results_crypto) > 0
    top_crypto = results_crypto[0]
    print(f"[OK] Query 3 matched: {top_crypto['cwe_id']} - {top_crypto['cwe_title']}")
    assert top_crypto["cwe_id"] == "CWE-328"

    print("\n[SUCCESS] ALL RAG RETRIEVAL TESTS PASSED (100% OK)!")


if __name__ == "__main__":
    test_rag_retrieval()
