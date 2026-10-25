"""
agent/nodes.py
State graph execution nodes for the LangGraph agent workflow:
1. parse_ast_node: Slices files into function chunks with exact line numbers.
2. scan_vulnerabilities_node: Scores risk and identifies suspicious code blocks.
3. rag_grounding_node: Fetches grounded CWE/OWASP evidence from local FAISS/RAG.
4. synthesize_fixes_node: Synthesizes side-by-side replacement fixes.
5. compile_report_node: Computes Health Score (0-100) and compiles AuditResult.
"""

import os
import ast
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from backend.schemas import (
    Finding, SeverityLevel, AuditSummary, DependencyGraph,
    GraphNode, GraphEdge, AuditResult, AuditStatus
)
from rag_engine.vector_store import rag_engine
from agent.state import AuditAgentState
from agent.llm_engine import generate_ai_remediation

try:
    from parser_engine.ast_slicer import ASTSlicer
    from parser_engine.graph_builder import GraphBuilder
    HAS_PARSER_ENGINE = True
except ImportError:
    HAS_PARSER_ENGINE = False


def check_polyglot_syntax(file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validates source code syntax across Python, JavaScript, Java, and C/C++.
    Returns discrete syntax error chunks for the audit pipeline.
    """
    rel_path = file_info["rel_path"]
    content = file_info.get("content", "").lstrip("\ufeff")
    lang = (file_info.get("language") or "").lower()
    ext = os.path.splitext(rel_path)[1].lower()
    errors = []
    lines = content.splitlines()

    # 1. Python Syntax & NameError Validation (via native ast.parse and AST symbol resolver)
    if ext in (".py", ".pyw") or lang == "python":
        parsed_tree = None
        try:
            parsed_tree = ast.parse(content, filename=rel_path)
        except SyntaxError as e:
            # Ignore false-positive errors caused by non-printable characters or BOM
            if "U+FEFF" in e.msg or "non-printable character" in e.msg:
                return []
            line_no = e.lineno or 1
            col_no = e.offset or 1
            err_text = (e.text or "").strip()
            # If the flagged line is a comment or blank, skip
            if err_text.startswith(("#", '"""', "'''")) or not err_text:
                return []
            errors.append({
                "file_path": rel_path,
                "function_name": f"<syntax_error_L{line_no}>",
                "line_start": line_no,
                "line_end": line_no,
                "code": err_text or (lines[line_no - 1] if line_no <= len(lines) else content[:100]),
                "language": "python",
                "complexity": 1,
                "docstring": "",
                "node_id": f"{rel_path}:syntax_error_L{line_no}",
                "syntax_error": f"Python SyntaxError: {e.msg} at line {line_no}, col {col_no}"
            })
            return errors

        if parsed_tree:
            # Check for undefined functions and typos of Python built-ins (e.g. priint -> print)
            COMMON_BUILTINS = {
                "print", "len", "range", "input", "str", "int", "float", "list", "dict",
                "set", "tuple", "bool", "open", "type", "sum", "min", "max", "abs",
                "round", "enumerate", "zip", "map", "filter", "sorted", "any", "all",
                "isinstance", "issubclass", "id", "dir", "help", "super", "vars",
                "hasattr", "getattr", "setattr", "delattr", "format", "eval", "exec",
                "repr", "iter", "next", "pow", "divmod", "bin", "oct", "hex", "ord", "chr"
            }
            defined = set()
            for node in ast.walk(parsed_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defined.add(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        defined.add(alias.asname or alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        defined.add(alias.asname or alias.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Param)):
                    defined.add(node.id)

            import difflib
            for node in ast.walk(parsed_tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name not in COMMON_BUILTINS and name not in defined and not name.startswith("_"):
                        matches = difflib.get_close_matches(name, COMMON_BUILTINS, n=1, cutoff=0.6)
                        if matches:
                            suggestion = matches[0]
                            line_no = node.lineno
                            col_no = getattr(node, "col_offset", 0) + 1
                            err_code = lines[line_no - 1].strip() if line_no <= len(lines) else content[:100]
                            errors.append({
                                "file_path": rel_path,
                                "function_name": f"<name_error_L{line_no}>",
                                "line_start": line_no,
                                "line_end": line_no,
                                "code": err_code,
                                "language": "python",
                                "complexity": 1,
                                "docstring": "",
                                "node_id": f"{rel_path}:name_error_L{line_no}",
                                "syntax_error": f"Python NameError: name '{name}' is not defined (Did you mean: '{suggestion}'?) at line {line_no}, col {col_no}"
                            })
                        elif len(lines) <= 5 and not defined and not name.isupper():
                            # Standalone raw snippet calling an unknown function
                            line_no = node.lineno
                            col_no = getattr(node, "col_offset", 0) + 1
                            err_code = lines[line_no - 1].strip() if line_no <= len(lines) else content[:100]
                            errors.append({
                                "file_path": rel_path,
                                "function_name": f"<name_error_L{line_no}>",
                                "line_start": line_no,
                                "line_end": line_no,
                                "code": err_code,
                                "language": "python",
                                "complexity": 1,
                                "docstring": "",
                                "node_id": f"{rel_path}:name_error_L{line_no}",
                                "syntax_error": f"Python NameError: name '{name}' is not defined at line {line_no}, col {col_no}"
                            })
        return errors

    # 2. JavaScript Validation (Node.js syntax check supporting ESM and CommonJS)
    if ext in (".js", ".mjs", ".cjs") or lang == "javascript":
        try:
            import subprocess
            # First attempt ESM module syntax check via node --input-type=module --check
            res_esm = subprocess.run(
                ["node", "--input-type=module", "--check"],
                input=content,
                text=True,
                capture_output=True,
                timeout=3
            )
            if res_esm.returncode == 0:
                return errors

            # If ESM check failed, test CommonJS via node --check (for top-level returns/arguments)
            res_cjs = subprocess.run(
                ["node", "--check"],
                input=content,
                text=True,
                capture_output=True,
                timeout=3
            )
            if res_cjs.returncode == 0:
                return errors

            # Both failed -> Genuine syntax error!
            err_text = res_esm.stderr if ("import " in content or "export " in content) else (res_cjs.stderr or res_esm.stderr)
            line_match = re.search(r'\[stdin\]:(\d+)', err_text)
            line_no = int(line_match.group(1)) if line_match else 1
            msg_match = re.search(r'(SyntaxError:[^\n\r]+)', err_text)
            msg = msg_match.group(1) if msg_match else "JavaScript SyntaxError"

            errors.append({
                "file_path": rel_path,
                "function_name": f"<syntax_error_L{line_no}>",
                "line_start": line_no,
                "line_end": line_no,
                "code": lines[line_no - 1] if line_no <= len(lines) else content[:100],
                "language": "javascript",
                "complexity": 1,
                "docstring": "",
                "node_id": f"{rel_path}:syntax_error_L{line_no}",
                "syntax_error": f"{msg} at line {line_no}"
            })
        except Exception:
            pass
        return errors

    # TypeScript and JSX files (.ts, .tsx, .jsx) rely on modern AST or compiler;
    # skip heuristic regex bracket counters to prevent false positives on JSX tags & type parameters
    if ext in (".ts", ".tsx", ".jsx") or "react" in lang or "typescript" in lang or ext in (".html", ".htm") or lang == "html":
        return errors

    # 3. Structural Bracket & Brace Matching (Only for Java and C/C++)
    if ext in (".java", ".c", ".cpp", ".cc", ".h", ".hpp") or lang in ("java", "c", "cpp"):
        # Strip block comments and strings across the file content to prevent false positives
        clean_content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean_content = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', clean_content)
        clean_lines = clean_content.splitlines()

        stack = []
        pairs = {')': '(', '}': '{', ']': '['}
        for idx, line in enumerate(clean_lines, 1):
            clean_line = re.sub(r'//.*$', '', line)
            for char in clean_line:
                if char in '({[':
                    stack.append((char, idx))
                elif char in ')}]':
                    if not stack:
                        errors.append({
                            "file_path": rel_path,
                            "function_name": f"<syntax_error_L{idx}>",
                            "line_start": idx,
                            "line_end": idx,
                            "code": lines[idx - 1].strip() if idx <= len(lines) else line.strip(),
                            "language": lang or "generic",
                            "complexity": 1,
                            "docstring": "",
                            "node_id": f"{rel_path}:syntax_error_L{idx}",
                            "syntax_error": f"SyntaxError: Unmatched closing bracket '{char}' at line {idx}"
                        })
                    else:
                        top, start_idx = stack.pop()
                        if top != pairs[char]:
                            errors.append({
                                "file_path": rel_path,
                                "function_name": f"<syntax_error_L{idx}>",
                                "line_start": idx,
                                "line_end": idx,
                                "code": lines[idx - 1].strip() if idx <= len(lines) else line.strip(),
                                "language": lang or "generic",
                                "complexity": 1,
                                "docstring": "",
                                "node_id": f"{rel_path}:syntax_error_L{idx}",
                                "syntax_error": f"SyntaxError: Mismatched bracket '{char}', expected match for '{top}' from line {start_idx}"
                            })

        for unclosed, start_idx in stack:
            errors.append({
                "file_path": rel_path,
                "function_name": f"<syntax_error_L{start_idx}>",
                "line_start": start_idx,
                "line_end": start_idx,
                "code": lines[start_idx - 1].strip() if start_idx <= len(lines) else "",
                "language": lang or "generic",
                "complexity": 1,
                "docstring": "",
                "node_id": f"{rel_path}:syntax_error_L{start_idx}",
                "syntax_error": f"SyntaxError: Unclosed opening bracket '{unclosed}' at line {start_idx}"
            })

    # 4. Java & C / C++ Statement Semicolon Verification
    if ext in (".java", ".c", ".cpp", ".cc", ".h", ".hpp") or lang in ("java", "c", "cpp"):
        statement_starters = (
            "System.out.", "return", "throw ", "import ", "package ", "break", "continue",
            "int ", "long ", "float ", "double ", "char ", "boolean ", "String ", "auto ", "const "
        )
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            clean = re.sub(r'//.*$', '', stripped).strip()
            if not clean or clean.startswith("/*") or clean.startswith("*"):
                continue

            if clean.endswith(("{", "}", ";", ",", ":", "\\")):
                continue
            if re.match(r'^(?:public|private|protected|static|final|class|interface|enum|default|case\b|@|#)', clean):
                if clean.endswith(")") and not any(clean.startswith(s) for s in ("System.out.", "return")):
                    continue
            if re.match(r'^(?:if|else|for|while|switch|try|catch|finally)\b', clean):
                continue

            is_statement = (
                any(clean.startswith(s) for s in statement_starters) or
                re.search(r'\b[a-zA-Z0-9_]+\s*=\s*[^;{]+$', clean) or
                re.search(r'\b(?:print|println|printf|log)\s*\([^)]*\)$', clean) or
                re.search(r'\.[a-zA-Z0-9_]+\s*\([^)]*\)$', clean)
            )

            if is_statement:
                errors.append({
                    "file_path": rel_path,
                    "function_name": f"<syntax_error_L{idx}>",
                    "line_start": idx,
                    "line_end": idx,
                    "code": stripped,
                    "language": lang or "java",
                    "complexity": 1,
                    "docstring": "",
                    "node_id": f"{rel_path}:syntax_error_L{idx}",
                    "syntax_error": f"SyntaxError: Missing semicolon ';' at end of statement at line {idx}"
                })

    return errors


def parse_ast_node(state: AuditAgentState) -> Dict[str, Any]:
    """Slices source files into discrete function chunks and extracts import/call links."""
    raw_files = state.get("raw_files", [])
    repo_name = state.get("repo_name", "")
    is_raw = bool(state.get("is_raw_code")) or repo_name in ("Raw Code Snippet", "raw-snippet") or repo_name.startswith("audit_raw_")
    
    # Strip any UTF-8 BOM from all raw files
    for f in raw_files:
        if "content" in f and isinstance(f["content"], str):
            f["content"] = f["content"].lstrip("\ufeff")

    function_chunks = []
    graph_nodes = []
    graph_edges = []

    # Priority 1: Use modular parser_engine (ASTSlicer & NetworkX GraphBuilder)
    if HAS_PARSER_ENGINE and raw_files:
        try:
            if not is_raw:
                builder = GraphBuilder(include_file_nodes=True)
                builder.build_from_raw_files(raw_files)
                pydantic_graph = builder.to_pydantic()
                graph_nodes = pydantic_graph.nodes
                graph_edges = pydantic_graph.edges
                file_functions = builder.file_functions
            else:
                # Slices without building whole-repo network graph for raw code
                slicer = ASTSlicer()
                file_functions = {}
                for f in raw_files:
                    file_functions[f["rel_path"]] = slicer.slice_code(f["content"], f["rel_path"])

            for rel_path, slices in file_functions.items():
                for s in slices:
                    lang = "python" if rel_path.endswith((".py", ".pyw")) else "javascript" if rel_path.endswith((".js", ".jsx", ".ts", ".tsx")) else "c"
                    function_chunks.append({
                        "file_path": s.file_path,
                        "function_name": s.name,
                        "line_start": s.line_start,
                        "line_end": s.line_end,
                        "code": s.code,
                        "language": lang,
                        "complexity": s.cyclomatic_complexity,
                        "docstring": s.docstring,
                        "node_id": s.node_id,
                    })

            # Also extract module-level scope (code outside functions: top-level secrets, configs, globals)
            for file_info in raw_files:
                rel_path = file_info["rel_path"]
                content = file_info.get("content", "")
                slices = file_functions.get(rel_path, [])
                func_lines = set()
                for s in slices:
                    func_lines.update(range(s.line_start, s.line_end + 1))
                
                lines = content.splitlines()
                module_lines = [line for i, line in enumerate(lines, 1) if i not in func_lines and line.strip()]
                if module_lines:
                    lang = "python" if rel_path.endswith((".py", ".pyw")) else "javascript" if rel_path.endswith((".js", ".jsx", ".ts", ".tsx")) else "text"
                    function_chunks.append({
                        "file_path": rel_path,
                        "function_name": "<module_scope>",
                        "line_start": 1,
                        "line_end": len(lines),
                        "code": "\n".join(module_lines),
                        "language": lang,
                        "complexity": 1,
                        "docstring": "",
                        "node_id": f"{rel_path}:<module_scope>"
                    })

            # Check for polyglot syntax errors across all source files (Python, Java, JS, C/C++)
            for file_info in raw_files:
                syntax_errs = check_polyglot_syntax(file_info)
                function_chunks.extend(syntax_errs)

            if function_chunks:
                return {
                    "function_chunks": function_chunks,
                    "dependency_graph": DependencyGraph(nodes=[] if is_raw else graph_nodes, edges=[] if is_raw else graph_edges),
                    "current_stage": "Parsed AST chunks" if is_raw else "Parsed AST and generated Call-Graph via parser_engine"
                }
        except Exception as e:
            # Fall back to inline parsing if unexpected error occurs
            function_chunks = []
            graph_nodes = []
            graph_edges = []

    # Priority 2: Built-in inline parsing fallback
    for file_info in raw_files:
        rel_path = file_info["rel_path"]
        content = file_info["content"]
        language = file_info["language"]

        # Add file node to graph
        file_node_id = rel_path
        graph_nodes.append(GraphNode(
            id=file_node_id,
            label=file_info.get("filename") or os.path.basename(rel_path),
            type="file",
            file_path=rel_path,
            risk_score=0.0
        ))

        if language == "python":
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        start_line = node.lineno
                        end_line = getattr(node, "end_lineno", start_line + len(node.body))
                        fn_lines = content.splitlines()[start_line - 1:end_line]
                        fn_code = "\n".join(fn_lines)

                        func_id = f"{rel_path}:{node.name}"
                        function_chunks.append({
                            "file_path": rel_path,
                            "function_name": node.name,
                            "line_start": start_line,
                            "line_end": end_line,
                            "code": fn_code,
                            "language": language
                        })

                        # Function graph node
                        graph_nodes.append(GraphNode(
                            id=func_id,
                            label=f"{node.name}()",
                            type="function",
                            file_path=rel_path,
                            risk_score=0.0
                        ))
                        # Edge from file to function
                        graph_edges.append(GraphEdge(
                            source=file_node_id,
                            target=func_id,
                            call_type="call"
                        ))

                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        # Dependency import edge
                        module_name = getattr(node, 'module', None)
                        if module_name:
                            graph_edges.append(GraphEdge(
                                source=file_node_id,
                                target=module_name,
                                call_type="import"
                            ))

            except SyntaxError:
                # Fallback line chunker if file has syntax errors
                lines = content.splitlines()
                function_chunks.append({
                    "file_path": rel_path,
                    "function_name": "module_root",
                    "line_start": 1,
                    "line_end": len(lines),
                    "code": content[:1500],
                    "language": language
                })
        else:
            # Multi-language regex function extractor for C/C++/JS/TS
            pattern = re.compile(r"(?:function\s+([a-zA-Z0-9_]+)|([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{)")
            matches = list(pattern.finditer(content))
            if matches:
                for match in matches:
                    name = match.group(1) or match.group(2) or "func"
                    start_char = match.start()
                    start_line = content[:start_char].count("\n") + 1
                    end_line = min(start_line + 25, len(content.splitlines()))
                    fn_code = "\n".join(content.splitlines()[start_line - 1:end_line])

                    func_id = f"{rel_path}:{name}"
                    function_chunks.append({
                        "file_path": rel_path,
                        "function_name": name,
                        "line_start": start_line,
                        "line_end": end_line,
                        "code": fn_code,
                        "language": language
                    })
                    graph_nodes.append(GraphNode(
                        id=func_id,
                        label=f"{name}()",
                        type="function",
                        file_path=rel_path,
                        risk_score=0.0
                    ))
                    graph_edges.append(GraphEdge(source=file_node_id, target=func_id, call_type="call"))
            else:
                function_chunks.append({
                    "file_path": rel_path,
                    "function_name": "global_scope",
                    "line_start": 1,
                    "line_end": min(len(content.splitlines()), 100),
                    "code": content[:1500],
                    "language": language
                })

    # Validate polyglot syntax across all raw files in Priority 2
    for file_info in raw_files:
        syntax_errs = check_polyglot_syntax(file_info)
        function_chunks.extend(syntax_errs)

    return {
        "function_chunks": function_chunks,
        "dependency_graph": DependencyGraph(nodes=[] if is_raw else graph_nodes, edges=[] if is_raw else graph_edges),
        "current_stage": "Parsed AST chunks" if is_raw else "Parsed AST and generated Call-Graph"
    }


def scan_vulnerabilities_node(state: AuditAgentState) -> Dict[str, Any]:
    """Analyzes function chunks to detect risky security patterns."""
    chunks = state.get("function_chunks", [])
    scanned_vulns = []

    # Detection rules matching CodeBERT / Devign vulnerability benchmarks
    rules = [
        {
            "category": "SQL Injection",
            # Supports f-strings, string concatenation (+), % formatting, and .format() on SQL statements
            "regex": (
                r"(?:(?:cursor|db|session|conn|connection)\.execute\s*\(\s*(?:f[\"'].*?\{|.*?%\s*\(|.*?\+|.*?\.format\s*\()|"
                r"execute\s*\(\s*f[\"'].*?\b(?:SELECT\b.*?\bFROM|INSERT\s+INTO|UPDATE\b.*?\bSET|DELETE\s+FROM)\b.*?\{|"
                r"f[\"'].*?\b(?:SELECT\b.*?\bFROM\b|INSERT\s+INTO\b|UPDATE\s+[a-zA-Z0-9_]+\s+SET\b|DELETE\s+FROM\b).*?\{|"
                r"[\"'].*?\b(?:SELECT\b.*?\bFROM|INSERT\s+INTO|UPDATE\b.*?\bSET|DELETE\s+FROM)\b.*?[\"']\s*(?:\+|\%|\.format\s*\())"
            ),
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.94
        },
        {
            "category": "Hardcoded Secret",
            # Matches explicit secret token patterns (AIza..., sk_test_, sk_live_, ghp_, AKIA, etc.) with or without quotes on any variable,
            # OR variable assignments of >=16 char strings to secret/key/token/password
            "regex": (
                r"(?:([A-Za-z0-9_]+)\s*=\s*['\"]?(?:AIza[0-9A-Za-z\-_]{35}|sk_live_[0-9a-zA-Z]{24,}|sk_test_[0-9a-zA-Z]{24,}|pk_live_[0-9a-zA-Z]{24,}|pk_test_[0-9a-zA-Z]{24,}|sk-[a-zA-Z0-9]{20,}|sk-proj-[a-zA-Z0-9_\-]{20,}|ghp_[0-9a-zA-Z_]{36,}|github_pat_[0-9a-zA-Z_]{36,}|AKIA[0-9A-Z]{16}|hf_[a-zA-Z0-9]{34,}|xox[baprs]-[0-9a-zA-Z-]{10,})['\"]?|"
                r"\b([A-Za-z0-9_]*(?:api_key|secret_key|secret_token|aws_secret|stripe_key|gemini_key|private_key|token|password))\b\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"])"
            ),
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.91
        },
        {
            "category": "OS Command Injection",
            # Detects os.system and os.popen with dynamic arguments or subprocess with shell=True
            "regex": r"(?:os\.(?:system|popen)\s*\(\s*(?:f[\"'].*?\{|.*?%|.*?\+)|subprocess\.(?:Popen|call|run)\s*\([^)]*shell\s*=\s*True)",
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.92
        },
        {
            "category": "Weak Cryptography",
            # Word boundaries around broken hash/crypto identifiers
            "regex": r"\b(hashlib\.md5|hashlib\.sha1|DES\.new|RC4)\b",
            "severity": SeverityLevel.MEDIUM,
            "base_conf": 0.84
        },
        {
            "category": "Insecure Deserialization",
            # pickle.load/loads or unsafe yaml.load
            "regex": r"\b(pickle\.loads?|yaml\.load\s*\([^,)]*\)(?!\s*,\s*Loader))\b",
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.88
        },
        {
            "category": "Path Traversal",
            "regex": r"(?:open\s*\([^)]*\.\./|send_from_directory\s*\([^)]*\+)",
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.87
        },
        {
            "category": "Cross-site Scripting (XSS)",
            # DOM-XSS, raw innerHTML/outerHTML injection, document.write, dangerouslySetInnerHTML
            "regex": (
                r"(?:\.(?:innerHTML|outerHTML)\s*=\s*(?:.*?\+|.*?`.*?\{|[a-zA-Z0-9_]+)|"
                r"document\.(?:write|writeln)\s*\(|"
                r"dangerouslySetInnerHTML\s*=|"
                r"(?:\$\([\"'].*?[\"']\)|jQuery\([\"'].*?[\"']\))\.html\s*\(\s*(?:.*?\+|[a-zA-Z0-9_]+))"
            ),
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.93
        },
        {
            "category": "Code Injection",
            # Dangerous dynamic code evaluation via eval(), exec(), new Function(), or string-based setTimeout/setInterval
            "regex": (
                r"(?:\b(?:eval|exec)\s*\([^)]+\)|"
                r"\bnew\s+Function\s*\([^)]+\)|"
                r"(?:setTimeout|setInterval)\s*\(\s*(?:['\"`].*?\+|['\"`][^'\"`]+['\"`]\s*,))"
            ),
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.95
        },
        {
            "category": "Server-Side Request Forgery (SSRF)",
            # Unvalidated user-supplied destinations in HTTP client calls
            "regex": (
                r"(?:requests\.(?:get|post|put|delete|patch)\s*\(\s*(?:[a-zA-Z0-9_]*url|[a-zA-Z0-9_]*target|req\.|request\.|params\.)|"
                r"urllib\.request\.urlopen\s*\(\s*(?:[a-zA-Z0-9_]*url|request\.|req\.)|"
                r"fetch\s*\(\s*(?:req\.|request\.|params\.|url|user_url|target_url)|"
                r"axios\.(?:get|post)\s*\(\s*(?:req\.|params\.|url|user_url))"
            ),
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.89
        },
        {
            "category": "Arbitrary File Upload",
            # Saving files using raw user-provided filenames without sanitization
            "regex": (
                r"(?:file\.save\s*\(\s*.*?file\.filename|"
                r"fs\.writeFile(?:Sync)?\s*\(\s*.*?file\.name)"
            ),
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.90
        },
        {
            "category": "Cross-Site Request Forgery (CSRF)",
            # State-changing actions performed over HTTP GET
            "regex": (
                r"(?:@app\.get\s*\(\s*[\"']/(?:transfer|delete|update|change_password|admin/action)|"
                r"router\.get\s*\(\s*[\"']/(?:transfer|delete|update|change_password))"
            ),
            "severity": SeverityLevel.HIGH,
            "base_conf": 0.86
        },
        {
            "category": "Buffer Overflow",
            # Unsafe legacy C string operations without buffer bounds
            "regex": r"\b(strcpy|strcat|sprintf|gets)\s*\(",
            "severity": SeverityLevel.CRITICAL,
            "base_conf": 0.95
        },
        {
            "category": "Integer Overflow",
            # Unchecked multiplication leading to undersized memory allocations
            "regex": r"\b(?:malloc|calloc)\s*\(\s*[a-zA-Z0-9_]+\s*\*\s*[a-zA-Z0-9_]+\s*\)",
            "severity": SeverityLevel.MEDIUM,
            "base_conf": 0.85
        }
    ]

    for chunk in chunks:
        if "syntax_error" in chunk:
            scanned_vulns.append({
                "chunk": chunk,
                "category": "Syntax Error",
                "severity": SeverityLevel.HIGH,
                "confidence": 1.0,
                "match_text": chunk["code"],
                "matched_var": None,
                "error_details": chunk.get("syntax_error")
            })
            continue

        code = chunk["code"]
        for rule in rules:
            match = re.search(rule["regex"], code, re.IGNORECASE)
            if match:
                groups = match.groups()
                matched_var = next((g for g in groups if g), None)
                scanned_vulns.append({
                    "chunk": chunk,
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "confidence": rule["base_conf"],
                    "match_text": match.group(0),
                    "matched_var": matched_var
                })
                break

    return {
        "scanned_vulnerabilities": scanned_vulns,
        "current_stage": f"Scanned {len(chunks)} functions, identified {len(scanned_vulns)} potential risks"
    }


FALLBACK_CWE_MAP = {
    "SQL Injection": {
        "cwe_id": "CWE-89",
        "cwe_title": "Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')",
        "owasp_category": "A03:2021 - Injection",
        "description": "The application constructs an SQL statement using raw user-controllable input without neutralization or parameterization, allowing an attacker to manipulate query structure and execute arbitrary SQL commands.",
        "mitigation": "Always use parameterized queries (prepared statements) or an Object-Relational Mapper (ORM) with parameterized bindings. Never concatenate or format strings directly into SQL queries.",
        "example_fix": "cursor.execute(\"SELECT * FROM users WHERE username = %s AND password = %s\", (user, pwd))"
    },
    "Hardcoded Secret": {
        "cwe_id": "CWE-798",
        "cwe_title": "Use of Hard-coded Credentials",
        "owasp_category": "A07:2021 - Identification and Authentication Failures",
        "description": "Hard-coding sensitive credentials, passwords, cryptographic keys, or API tokens directly within source code exposes them to anyone with repository access.",
        "mitigation": "Store credentials outside of source code using environment variables, cloud key vaults (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault), or configuration files listed in .gitignore.",
        "example_fix": "API_KEY = os.getenv('STRIPE_API_KEY')\nif not API_KEY:\n    raise ValueError('Missing required environment variable STRIPE_API_KEY')"
    },
    "Weak Cryptography": {
        "cwe_id": "CWE-328",
        "cwe_title": "Use of Weak Hash / Broken Cryptographic Algorithm",
        "owasp_category": "A02:2021 - Cryptographic Failures",
        "description": "The application uses a broken or risky cryptographic hash algorithm (e.g. MD5, SHA-1, DES, RC4) susceptible to collision attacks or trivial reverse cracking.",
        "mitigation": "Upgrade to secure modern cryptographic hashing algorithms such as SHA-256/SHA-512, or purpose-built password hashing functions like bcrypt, scrypt, or Argon2id.",
        "example_fix": "hashlib.sha256(data.encode('utf-8')).hexdigest()"
    },
    "OS Command Injection": {
        "cwe_id": "CWE-78",
        "cwe_title": "Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')",
        "owasp_category": "A03:2021 - Injection",
        "description": "The application constructs an operating system command using unvalidated user input and executes it via a shell, enabling attackers to execute arbitrary system-level commands.",
        "mitigation": "Avoid executing OS shell commands when library APIs exist. If subprocess execution is required, pass arguments as a structured array without shell=True.",
        "example_fix": "subprocess.run(['command', arg1, arg2], check=True, shell=False)"
    },
    "Insecure Deserialization": {
        "cwe_id": "CWE-502",
        "cwe_title": "Deserialization of Untrusted Data",
        "owasp_category": "A08:2021 - Software and Data Integrity Failures",
        "description": "The application deserializes untrusted data without verification. Serialized object representations can contain bytecode instructions leading to arbitrary remote code execution.",
        "mitigation": "Do not deserialize untrusted data using formats that support arbitrary code execution (e.g., pickle). Use safe serialization standards such as JSON or Protocol Buffers.",
        "example_fix": "payload = json.loads(untrusted_stream.decode('utf-8'))"
    },
    "Path Traversal": {
        "cwe_id": "CWE-22",
        "cwe_title": "Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')",
        "owasp_category": "A01:2021 - Broken Access Control",
        "description": "The application uses external input to construct a pathname intended to identify a file or directory located under a restricted directory, but does not properly neutralize sequences like '../'.",
        "mitigation": "Validate path input against an allowlist, use safe path resolution methods, and prevent path separators or relative directory navigation.",
        "example_fix": "safe_path = os.path.join(base_dir, os.path.basename(user_path))"
    },
    "Syntax Error": {
        "cwe_id": "CWE-754",
        "cwe_title": "Improper Check for Unusual or Exceptional Conditions (Syntax Error)",
        "owasp_category": "A08:2021 - Software and Data Integrity Failures",
        "description": "The file contains a syntax violation preventing compilation or execution.",
        "mitigation": "Correct the syntax error (check unclosed brackets, missing colons, or improper indentation).",
        "example_fix": "# Correct syntax error"
    },
    "Cross-site Scripting (XSS)": {
        "cwe_id": "CWE-79",
        "cwe_title": "Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting - XSS')",
        "owasp_category": "A03:2021 - Injection",
        "description": "The application receives untrusted input and includes it in a web page without proper validation or encoding, allowing malicious scripts to execute in a victim's browser context.",
        "mitigation": "Use context-aware output encoding (e.g. textContent instead of innerHTML), modern template engines with auto-escaping, and enforce Content Security Policy (CSP).",
        "example_fix": "element.textContent = 'Welcome ' + user_name;"
    },
    "Code Injection": {
        "cwe_id": "CWE-94",
        "cwe_title": "Improper Control of Generation of Code ('Code Injection')",
        "owasp_category": "A03:2021 - Injection",
        "description": "The application receives untrusted input and passes it to dynamic evaluation functions (e.g., Python eval, exec, JavaScript eval), allowing arbitrary code execution in the application context.",
        "mitigation": "Never use eval() or exec() with untrusted user input. Use safe data parsing libraries (such as json.loads or JSON.parse).",
        "example_fix": "// JavaScript: JSON.parse(userInput) | Python: json.loads(user_input)"
    },
    "Server-Side Request Forgery (SSRF)": {
        "cwe_id": "CWE-918",
        "cwe_title": "Server-Side Request Forgery ('SSRF')",
        "owasp_category": "A10:2021 - Server-Side Request Forgery",
        "description": "The web server receives a URL from an untrusted user and makes a network request to that URL without validating the destination, allowing internal network reconnaissance or cloud metadata theft.",
        "mitigation": "Enforce strict allowlists of acceptable hostnames/domains. Reject loopback and private IP ranges (127.0.0.1, 169.254.169.254, 10.0.0.0/8).",
        "example_fix": "validate_safe_url(target_url)\nresponse = requests.get(target_url, timeout=5)"
    },
    "Arbitrary File Upload": {
        "cwe_id": "CWE-434",
        "cwe_title": "Unrestricted Upload of File with Dangerous Type",
        "owasp_category": "A08:2021 - Software and Data Integrity Failures",
        "description": "The software allows uploading files of dangerous types that can be directly executed within the server environment.",
        "mitigation": "Validate file extensions against an allowlist, verify MIME types, generate randomized unique filenames, and store uploaded files outside the web root.",
        "example_fix": "safe_filename = f'{uuid.uuid4()}{ext}'"
    },
    "Cross-Site Request Forgery (CSRF)": {
        "cwe_id": "CWE-352",
        "cwe_title": "Cross-Site Request Forgery ('CSRF')",
        "owasp_category": "A01:2021 - Broken Access Control",
        "description": "The web application does not verify whether a state-changing request was intentionally provided by the authenticated user.",
        "mitigation": "Use anti-CSRF tokens for state-changing requests, configure SameSite=Lax/Strict on session cookies, and enforce custom request headers.",
        "example_fix": "@app.post('/transfer')\ndef transfer(amount, csrf_token = Depends(verify_csrf)): ..."
    },
    "Buffer Overflow": {
        "cwe_id": "CWE-787",
        "cwe_title": "Out-of-bounds Write ('Buffer Overflow')",
        "owasp_category": "A06:2021 - Vulnerable and Outdated Components",
        "description": "The software writes data past the end, or before the beginning, of the intended buffer in C/C++, causing memory corruption or arbitrary code execution.",
        "mitigation": "Use bounds-checking functions (strncpy, snprintf), avoid raw pointer arithmetic without bounds checks, or use memory-safe abstractions.",
        "example_fix": "snprintf(buffer, sizeof(buffer), \"%s\", user_input);"
    },
    "Integer Overflow": {
        "cwe_id": "CWE-190",
        "cwe_title": "Integer Overflow or Wraparound",
        "owasp_category": "A06:2021 - Vulnerable and Outdated Components",
        "description": "The software performs an integer calculation that can produce an integer overflow or wraparound, resulting in unexpected values used for memory allocation sizes.",
        "mitigation": "Check for integer overflow before arithmetic operations that calculate buffer sizes or loop counters.",
        "example_fix": "if (size > 0 && count > SIZE_MAX / size) return ERROR_OVERFLOW;"
    }
}


def rag_grounding_node(state: AuditAgentState) -> Dict[str, Any]:
    """Queries local FAISS Vector RAG Engine for grounded CWE standards, or uses direct standard mapping if RAG disabled."""
    enable_rag = state.get("enable_rag", True)
    scanned_vulns = state.get("scanned_vulnerabilities", [])
    grounded_evidence = []

    for item in scanned_vulns:
        chunk = item["chunk"]
        category = item["category"]

        if category == "Syntax Error":
            matched_cwe = dict(FALLBACK_CWE_MAP["Syntax Error"])
            if item.get("error_details"):
                matched_cwe["description"] = item["error_details"]
        elif enable_rag:
            # Sub-millisecond vector similarity search in FAISS
            retrieved_docs = rag_engine.retrieve(
                query=chunk["code"][:300],
                category_hint=category,
                top_k=1
            )
            matched_cwe = retrieved_docs[0] if retrieved_docs else FALLBACK_CWE_MAP.get(category, {
                "cwe_id": "CWE-699",
                "cwe_title": "Software Development Weakness",
                "description": "General security pattern deviation.",
                "mitigation": "Review code against secure coding principles.",
                "example_fix": "# Review and apply validation"
            })
        else:
            # Direct static mapping when FAISS Vector RAG is disabled
            matched_cwe = FALLBACK_CWE_MAP.get(category, {
                "cwe_id": "CWE-699",
                "cwe_title": "Software Development Weakness",
                "description": "General security pattern deviation.",
                "mitigation": "Review code against secure coding principles.",
                "example_fix": "# Review and apply validation"
            })

        grounded_evidence.append({
            **item,
            "cwe_doc": matched_cwe
        })

    stage_desc = f"Grounded {len(grounded_evidence)} items with authoritative CWE standards" if enable_rag else f"Mapped {len(grounded_evidence)} items to CWE standards (FAISS bypassed)"
    return {
        "grounded_evidence": grounded_evidence,
        "current_stage": stage_desc
    }


def _generate_contextual_fix(
    category: str,
    code: str,
    cwe: Dict[str, Any],
    matched_var: Optional[str] = None,
    language: Optional[str] = None,
    file_path: Optional[str] = None
) -> str:
    """Generates a contextual grounded replacement code diff instead of generic templates."""
    cwe_id = cwe.get("cwe_id", "CWE-SEC")
    fix_suggestion = cwe.get("example_fix", "# Apply secure coding pattern")

    ext = os.path.splitext(file_path or "")[1].lower()
    is_js_or_html = (
        language in ("javascript", "typescript", "html") or
        ext in (".js", ".jsx", ".ts", ".tsx", ".html", ".htm")
    )
    comment_char = "//" if (is_js_or_html or ext in (".java", ".c", ".cpp")) else "#"

    if category == "Weak Cryptography":
        if "hashlib.md5" in code:
            replaced = re.sub(r"hashlib\.md5\((.*?)\)", r"hashlib.sha256(\1)", code)
            return f"# Grounded Fix ({cwe_id}): Replace MD5 with SHA-256 (or bcrypt/argon2 for passwords)\n" + replaced
        elif "hashlib.sha1" in code:
            replaced = re.sub(r"hashlib\.sha1\((.*?)\)", r"hashlib.sha256(\1)", code)
            return f"# Grounded Fix ({cwe_id}): Replace deprecated SHA-1 with SHA-256\n" + replaced

    elif category == "Hardcoded Secret":
        target_var = matched_var or "API_KEY"
        env_var = "API_KEY"
        if "AIza" in code:
            env_var = "GEMINI_API_KEY"
        elif "sk_live" in code or "sk_test" in code:
            env_var = "STRIPE_API_KEY"
        elif "ghp_" in code or "github_pat" in code:
            env_var = "GITHUB_TOKEN"
        elif "AKIA" in code or "aws" in code.lower():
            env_var = "AWS_SECRET_KEY"
        elif matched_var and len(matched_var) > 2:
            env_var = matched_var.upper()

        return (
            f"import os\n"
            f"# Grounded Fix ({cwe_id}): Read sensitive credential from environment variables\n"
            f"{target_var} = os.getenv('{env_var}')\n"
            f"if not {target_var}:\n"
            f"    raise ValueError('Missing required environment variable {env_var}')"
        )

    elif category == "Insecure Deserialization":
        if "pickle.loads" in code:
            replaced = re.sub(r"pickle\.loads\((.*?)\)", r"json.loads(\1.decode('utf-8') if isinstance(\1, bytes) else \1)", code)
            return f"import json\n# Grounded Fix ({cwe_id}): Avoid pickle; use secure JSON or Protocol Buffers\n" + replaced

    elif category == "OS Command Injection":
        if "os.system" in code or "os.popen" in code:
            if "ping" in code:
                match = re.search(r'ping\s+(?:-[a-zA-Z0-9]+\s+[a-zA-Z0-9]+\s+)*\{([a-zA-Z0-9_]+)\}', code)
                var = match.group(1) if match else "ip"
                return (
                    f"import subprocess\n"
                    f"# Grounded Fix ({cwe_id}): Avoid shell execution; pass argument list to subprocess.run\n"
                    f"def run_ping({var}):\n"
                    f"    res = subprocess.run(['ping', '-c', '1', {var}], capture_output=True, text=True)\n"
                    f"    return res.stdout"
                )
            return (
                f"import subprocess\n"
                f"# Grounded Fix ({cwe_id}): Avoid os.system/popen; execute subprocess with structured arguments without shell=True\n"
                f"# Example: subprocess.run(['command', arg1, arg2], check=True, shell=False)"
            )

    elif category == "SQL Injection":
        placeholder = "?" if ("sqlite" in code.lower() or "sqlite3" in code.lower() or "db" in code.lower() or ":memory:" in code.lower()) else "%s"
        code_fixed = code

        # 1. Direct execution: (db|cursor|conn|session).execute(f"SELECT ...")
        def replace_exec(match):
            caller = match.group(1)
            sql_str = match.group(2)
            vars_found = re.findall(r"\{([a-zA-Z0-9_\.\[\]]+)\}", sql_str)
            if not vars_found:
                return match.group(0)
            clean_sql = re.sub(r"['\"]?\{[a-zA-Z0-9_\.\[\]]+\}['\"]?", placeholder, sql_str)
            params_tuple = f"({', '.join(vars_found)}{',' if len(vars_found) == 1 else ''})"
            return f'{caller}.execute("{clean_sql}", {params_tuple})'

        code_fixed = re.sub(r'([a-zA-Z0-9_]+)\.execute\s*\(\s*f["\'](.*?)["\']\s*\)', replace_exec, code_fixed)

        # 2. Query variable assignment: query = f"SELECT ..." followed by (caller).execute(query)
        def replace_query_var(match):
            var_name = match.group(1)
            sql_str = match.group(2)
            caller = match.group(3)
            vars_found = re.findall(r"\{([a-zA-Z0-9_\.\[\]]+)\}", sql_str)
            if not vars_found:
                return match.group(0)
            clean_sql = re.sub(r"['\"]?\{[a-zA-Z0-9_\.\[\]]+\}['\"]?", placeholder, sql_str)
            params_tuple = f"({', '.join(vars_found)}{',' if len(vars_found) == 1 else ''})"
            return f'{var_name} = "{clean_sql}"\n    # Grounded Fix ({cwe_id}): Parameterized query bindings\n    {caller}.execute({var_name}, {params_tuple})'

        code_fixed = re.sub(
            r'([a-zA-Z0-9_]+)\s*=\s*f["\'](.*?)["\']\s*\n\s*([a-zA-Z0-9_]+)\.execute\(\1\)',
            replace_query_var,
            code_fixed
        )

        # 3. String concatenation: query = "SELECT ... " + var
        def replace_concat(match):
            var_name = match.group(1)
            sql_head = match.group(2)
            var_injected = match.group(3)
            clean_sql = re.sub(r"['\"]?\s*$", "", sql_head).strip() + " " + placeholder
            return f'{var_name} = "{clean_sql}"\n    # Grounded Fix ({cwe_id}): Parameterized query bindings\n    cursor.execute({var_name}, ({var_injected},))'

        code_fixed = re.sub(
            r'([a-zA-Z0-9_]+)\s*=\s*["\'](SELECT\b.*?FROM\b.*?WHERE\b.*?=)\s*["\']\s*\+\s*([a-zA-Z0-9_]+)',
            replace_concat,
            code_fixed,
            flags=re.IGNORECASE
        )

        # 4. String formatting %: query = "SELECT ... WHERE x = %s" % (var,)
        def replace_percent(match):
            var_name = match.group(1)
            sql_head = match.group(2)
            vars_injected = match.group(3)
            clean_sql = sql_head.replace("%s", placeholder).replace("%d", placeholder)
            return f'{var_name} = "{clean_sql}"\n    # Grounded Fix ({cwe_id}): Pass tuple to cursor.execute instead of string % operator\n    cursor.execute({var_name}, {vars_injected})'

        code_fixed = re.sub(
            r'([a-zA-Z0-9_]+)\s*=\s*["\'](SELECT\b.*?FROM\b.*?WHERE\b.*?)\s*["\']\s*%\s*(\([^)]+\)|[a-zA-Z0-9_]+)',
            replace_percent,
            code_fixed,
            flags=re.IGNORECASE
        )

        if code_fixed != code:
            return f"# Grounded Fix ({cwe_id}): Use parameterized query with safe placeholder bindings\n" + code_fixed

    elif category == "Cross-site Scripting (XSS)":
        if ".innerHTML" in code:
            if any(tag in code for tag in ("<tr", "<td", "<div", "<span", "<table", "<p", "</")):
                return (
                    f"// Grounded Fix ({cwe_id}): Use DOMPurify.sanitize() or document.createElement() to prevent XSS\n"
                    f"// Example: element.innerHTML = DOMPurify.sanitize(htmlMarkup);\n"
                    f"{code}"
                )
            fixed = code.replace(".innerHTML", ".textContent")
            return f"// Grounded Fix ({cwe_id}): Use textContent instead of innerHTML to prevent script execution\n" + fixed
        elif ".outerHTML" in code:
            return (
                f"// Grounded Fix ({cwe_id}): Sanitize HTML markup or manipulate DOM nodes directly\n"
                f"// Example: element.outerHTML = DOMPurify.sanitize(markup);\n"
                f"{code}"
            )
        elif "document.write" in code:
            return f"// Grounded Fix ({cwe_id}): Avoid document.write(); manipulate textContent on target element instead\n" + code

    elif category == "Code Injection":
        if is_js_or_html:
            if "eval(" in code:
                fixed = code.replace("eval(", "JSON.parse(")
                return f"// Grounded Fix ({cwe_id}): Avoid dynamic eval(); parse data with structured JSON.parse()\n" + fixed
            return (
                f"// Grounded Fix ({cwe_id}): Avoid dynamic code execution; use structured JSON parsing or callback functions\n"
                f"const parsedData = JSON.parse(userInput);"
            )
        else:
            if "eval(" in code:
                fixed = code.replace("eval(", "json.loads(")
                return f"# Grounded Fix ({cwe_id}): Avoid dynamic eval(); parse data with structured json.loads()\n" + fixed
            return (
                f"# Grounded Fix ({cwe_id}): Avoid dynamic execution; parse structured data safely\n"
                f"import json\nresult = json.loads(user_input)"
            )

    elif category == "Buffer Overflow":
        if "strcpy(" in code:
            fixed = re.sub(r"strcpy\s*\(\s*([a-zA-Z0-9_]+)\s*,\s*([a-zA-Z0-9_]+)\s*\)", r"strncpy(\1, \2, sizeof(\1) - 1);\n    \1[sizeof(\1) - 1] = '\\0'", code)
            return f"// Grounded Fix ({cwe_id}): Use bounded strncpy with null-termination\n" + fixed

    elif category == "Syntax Error":
        stripped = code.strip()
        # If line is a comment or blank, leave it as is
        if stripped.startswith(("#", "//", "/*", "*", '"""', "'''")):
            return f"// Non-executable comment or documentation line\n" + code

        # NameError / typo fix (e.g. priint -> print)
        search_scope = str(fix_suggestion) + " " + str(cwe.get("description", ""))
        name_error_match = re.search(r"name\s+'([a-zA-Z0-9_]+)'\s+is\s+not\s+defined\s+\(Did you mean:\s+'([a-zA-Z0-9_]+)'\?\)", search_scope)
        if name_error_match:
            wrong_name = name_error_match.group(1)
            correct_name = name_error_match.group(2)
            fixed_code = re.sub(r'\b' + re.escape(wrong_name) + r'\b', correct_name, code)
            return f"# Grounded Fix ({cwe_id}): Corrected undefined symbol typo ('{wrong_name}' -> '{correct_name}')\n" + fixed_code

        if "missing semicolon" in str(fix_suggestion).lower() or ("semicolon" in str(cwe.get("description", "")).lower()):
            if not code.rstrip().endswith(";"):
                return f"// Grounded Fix ({cwe_id}): Added missing semicolon\n" + code.rstrip() + ";"
        if "(" in code and ")" not in code and ":" in code and not stripped.startswith(("#", "//")):
            fixed = re.sub(r":\s*$", "):", code)
            return f"# Grounded Fix ({cwe_id}): Corrected syntax violation (closed missing parenthesis)\n" + fixed
        return f"{comment_char} Grounded Fix ({cwe_id}): Review and correct syntax\n" + code

    return f"{comment_char} Grounded Fix ({cwe_id}):\n" + fix_suggestion


def synthesize_fixes_node(state: AuditAgentState) -> Dict[str, Any]:
    """Generates side-by-side replacement code diffs and explanation with parallel worker speedup."""
    grounded_evidence = state.get("grounded_evidence", [])
    findings: List[Finding] = []
    graph = state.get("dependency_graph", DependencyGraph())
    node_risk_map = {}

    import concurrent.futures

    # Cache to avoid duplicate LLM calls for identical vulnerability patterns across multiple files
    remediation_cache: Dict[Any, str] = {}

    def process_item(item_idx: int, item: Dict[str, Any]) -> Tuple[int, Dict[str, Any], str]:
        chunk = item["chunk"]
        cwe = item["cwe_doc"]
        category = item["category"]
        original_code = chunk["code"]
        matched_var = item.get("matched_var")
        lang = chunk.get("language")
        file_path = chunk.get("file_path", "")

        # Create cache key to reuse fixes for identical repeated patterns
        cache_key = (category, cwe.get("cwe_id"), original_code[:120].strip())
        if cache_key in remediation_cache:
            return item_idx, item, remediation_cache[cache_key]

        fix_code = None
        # Call AI for top 30 findings (high-speed generation with Gemini 2.5 Flash)
        if item_idx <= 30:
            try:
                fix_code = generate_ai_remediation(
                    category=category,
                    cwe_id=cwe["cwe_id"],
                    vulnerable_code=original_code,
                    file_path=file_path,
                    error_details=cwe.get("description"),
                    language=lang
                )
            except Exception:
                pass

        # Fallback to instantaneous deterministic AST patch generator
        if not fix_code:
            fix_code = _generate_contextual_fix(
                category=category,
                code=original_code,
                cwe=cwe,
                matched_var=matched_var,
                language=lang,
                file_path=file_path
            )

        remediation_cache[cache_key] = fix_code
        return item_idx, item, fix_code

    # Execute with ThreadPoolExecutor (max_workers=5) for 5x-10x speedup
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_item, i, item) for i, item in enumerate(grounded_evidence, 1)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # Sort back into original order
    results.sort(key=lambda r: r[0])

    for i, item, fix_code in results:
        chunk = item["chunk"]
        cwe = item["cwe_doc"]
        finding_id = f"FIND-{i:03d}"
        category = item["category"]
        original_code = chunk["code"]

        finding = Finding(
            id=finding_id,
            file_path=chunk["file_path"],
            line_start=chunk["line_start"],
            line_end=chunk["line_end"],
            function_name=chunk.get("function_name"),
            category=category,
            severity=item["severity"],
            confidence=item["confidence"],
            cwe_id=cwe["cwe_id"],
            cwe_title=cwe["cwe_title"],
            description=cwe["description"],
            vulnerable_code=original_code,
            fix_code=fix_code,
            explanation=f"Grounded in {cwe.get('owasp_category', 'OWASP Top 10')} & {cwe['cwe_id']}: {cwe['mitigation']}"
        )
        findings.append(finding)

        # Mark function risk score
        func_id = f"{chunk['file_path']}:{chunk.get('function_name', '')}"
        node_risk_map[func_id] = (item["confidence"], item["severity"])
        node_risk_map[chunk["file_path"]] = (item["confidence"], item["severity"])

    # Update graph nodes with predicted risk
    for node in graph.nodes:
        if node.id in node_risk_map:
            score, sev = node_risk_map[node.id]
            node.risk_score = score
            node.severity = sev

    return {
        "grounded_findings": findings,
        "dependency_graph": graph,
        "current_stage": f"Synthesized {len(findings)} side-by-side replacement fixes"
    }


def compile_report_node(state: AuditAgentState) -> Dict[str, Any]:
    """Computes Security Health Score (0-100) and compiles AuditResult."""
    findings = state.get("grounded_findings", [])
    raw_files = state.get("raw_files", [])
    chunks = state.get("function_chunks", [])
    graph = state.get("dependency_graph", DependencyGraph())
    repo_name = state.get("repo_name", "audited-repo")
    is_raw = bool(state.get("is_raw_code")) or repo_name in ("Raw Code Snippet", "raw-snippet") or repo_name.startswith("audit_raw_")

    if is_raw:
        graph = DependencyGraph(nodes=[], edges=[])

    # Calculate severity breakdown
    crit = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
    high = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
    med = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
    low = sum(1 for f in findings if f.severity == SeverityLevel.LOW)

    # Health score formula: 100 - (crit*20 + high*10 + med*5 + low*2)
    deduction = (crit * 20) + (high * 10) + (med * 5) + (low * 2)
    health_score = max(0, 100 - deduction)

    summary = AuditSummary(
        critical_count=crit,
        high_count=high,
        medium_count=med,
        low_count=low,
        total_findings=len(findings)
    )

    audit_result = AuditResult(
        audit_id=str(uuid.uuid4()),
        repo_name=repo_name,
        status=AuditStatus.COMPLETED,
        health_score=health_score,
        total_files=len(raw_files),
        total_functions=len(chunks),
        scanned_at=datetime.utcnow().isoformat() + "Z",
        summary=summary,
        findings=findings,
        dependency_graph=graph
    )

    return {
        "audit_result": audit_result,
        "health_score": health_score,
        "current_stage": "Audit Complete"
    }
