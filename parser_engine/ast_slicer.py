"""
parser_engine/ast_slicer.py
AST-based function slicer, boundary identifier, and complexity metric extractor.
Supports deterministic slicing for Python and heuristic slicing for other languages.
"""

import ast
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Union


@dataclass
class FunctionSlice:
    """Represents a discrete function block extracted from source code."""
    name: str
    signature: str
    file_path: str
    line_start: int
    line_end: int
    boundary: str
    docstring: Optional[str]
    cyclomatic_complexity: int
    arg_count: int
    args: List[str]
    lines_of_code: int
    code: str
    calls: List[str] = field(default_factory=list)
    class_name: Optional[str] = None
    is_async: bool = False
    return_annotation: Optional[str] = None
    decorators: List[str] = field(default_factory=list)

    @property
    def node_id(self) -> str:
        """Normalized unique node ID: 'filename.py:func' or 'filename.py:Class.func'."""
        norm_path = self.file_path.replace("\\", "/")
        prefix = f"{self.class_name}." if self.class_name else ""
        return f"{norm_path}:{prefix}{self.name}"

    @property
    def line_range(self) -> str:
        """Formatted line range: 'L<start>-L<end>'."""
        return f"L{self.line_start}-L{self.line_end}"

    @property
    def full_boundary(self) -> str:
        """Full path boundary: 'path/to/file.py:L<start>-L<end>'."""
        norm_path = self.file_path.replace("\\", "/")
        return f"{norm_path}:L{self.line_start}-L{self.line_end}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize function slice to a dictionary matching pipeline requirements."""
        return {
            "name": self.name,
            "function_name": self.name,
            "signature": self.signature,
            "file_path": self.file_path.replace("\\", "/"),
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_range": self.line_range,
            "boundary": self.boundary,
            "docstring": self.docstring,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "arg_count": self.arg_count,
            "args": self.args,
            "lines_of_code": self.lines_of_code,
            "code": self.code,
            "calls": self.calls,
            "class_name": self.class_name,
            "is_async": self.is_async,
            "return_annotation": self.return_annotation,
            "decorators": self.decorators,
            "node_id": self.node_id,
        }


@dataclass
class FileSliceResult:
    """Represents the complete slicing result for a single source file."""
    file_path: str
    language: str
    functions: List[FunctionSlice] = field(default_factory=list)
    imports: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    total_lines: int = 0
    lines_of_code: int = 0
    syntax_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path.replace("\\", "/"),
            "language": self.language,
            "functions": [f.to_dict() for f in self.functions],
            "imports": self.imports,
            "classes": self.classes,
            "total_lines": self.total_lines,
            "lines_of_code": self.lines_of_code,
            "syntax_valid": self.syntax_valid,
            "error_message": self.error_message,
        }


class _CyclomaticComplexityVisitor(ast.NodeVisitor):
    """Calculates McCabe cyclomatic complexity within a single function AST."""

    def __init__(self):
        # Base complexity is 1 (linearly independent path through code)
        self.complexity = 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Do not enter nested functions (they have their own complexity)
        pass

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Do not enter nested async functions
        pass

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # Each operand beyond the first introduces an alternate branching condition
        self.complexity += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        # Comprehension loop introduces a branch, plus each filter if clause
        self.complexity += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_Match(self, node: Any) -> None:
        # Python 3.10+ pattern matching
        cases = getattr(node, "cases", [])
        self.complexity += max(1, len(cases))
        self.generic_visit(node)


class _FunctionCallVisitor(ast.NodeVisitor):
    """Extracts function and method call names inside a function AST."""

    def __init__(self):
        self.calls: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Do not enter nested functions
        pass

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Do not enter nested async functions
        pass

    def visit_Call(self, node: ast.Call) -> None:
        name = self._resolve_call_name(node.func)
        if name and name not in self.calls:
            self.calls.append(name)
        self.generic_visit(node)

    def _resolve_call_name(self, func_node: ast.AST) -> Optional[str]:
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            base = self._resolve_call_name(func_node.value)
            if base:
                return f"{base}.{func_node.attr}"
            return func_node.attr
        return None


class ASTSlicer:
    """
    Performs deterministic AST function boundary slicing, signature parsing,
    cyclomatic complexity analysis, and call-site extraction.
    """

    def __init__(self, include_decorators: bool = True):
        self.include_decorators = include_decorators

    def slice_code(
        self,
        code: str,
        file_path: str = "module.py",
        language: str = "python",
    ) -> List[FunctionSlice]:
        """
        Slices source code into discrete function blocks with exact line ranges.

        Args:
            code: Source code content.
            file_path: Relative file path for boundary identification.
            language: Programming language (default: 'python').

        Returns:
            List of FunctionSlice objects.
        """
        norm_path = file_path.replace("\\", "/")
        if language.lower() == "python":
            try:
                tree = ast.parse(code, filename=norm_path)
                return self._slice_python_ast(tree, code, norm_path)
            except SyntaxError as e:
                # Graceful fallback to regex slicing on syntax error
                return self._slice_fallback_regex(code, norm_path, language, syntax_err=str(e))
        else:
            return self._slice_fallback_regex(code, norm_path, language)

    def slice_file(self, file_path: str) -> List[FunctionSlice]:
        """Slices a source file on disk into function blocks."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
        lang = self._detect_language(file_path)
        return self.slice_code(code, file_path=file_path, language=lang)

    def parse_file_detailed(self, file_path: str, content: Optional[str] = None) -> FileSliceResult:
        """
        Parses a file returning functions, imports, class definitions, and file metrics.
        """
        norm_path = file_path.replace("\\", "/")
        if content is None:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

        lang = self._detect_language(norm_path)
        lines = content.splitlines()
        total_lines = len(lines)
        loc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

        if lang == "python":
            try:
                tree = ast.parse(content, filename=norm_path)
                functions = self._slice_python_ast(tree, content, norm_path)
                imports = self._extract_python_imports(tree)
                classes = self._extract_python_classes(tree)
                return FileSliceResult(
                    file_path=norm_path,
                    language=lang,
                    functions=functions,
                    imports=imports,
                    classes=classes,
                    total_lines=total_lines,
                    lines_of_code=loc,
                    syntax_valid=True,
                )
            except SyntaxError as e:
                fallback_funcs = self._slice_fallback_regex(content, norm_path, lang, syntax_err=str(e))
                return FileSliceResult(
                    file_path=norm_path,
                    language=lang,
                    functions=fallback_funcs,
                    total_lines=total_lines,
                    lines_of_code=loc,
                    syntax_valid=False,
                    error_message=str(e),
                )
        else:
            funcs = self._slice_fallback_regex(content, norm_path, lang)
            return FileSliceResult(
                file_path=norm_path,
                language=lang,
                functions=funcs,
                total_lines=total_lines,
                lines_of_code=loc,
                syntax_valid=True,
            )

    def slice_directory(
        self,
        root_dir: str,
        extensions: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
    ) -> Dict[str, List[FunctionSlice]]:
        """
        Recursively scans a directory and slices all discovered source files.

        Returns:
            Dictionary mapping relative file paths to their lists of FunctionSlice.
        """
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".c", ".cpp", ".h", ".go"]
        if exclude_dirs is None:
            exclude_dirs = [".git", "venv", ".venv", "env", "node_modules", "__pycache__", "checkpoints", "dist", "build"]

        results: Dict[str, List[FunctionSlice]] = {}
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                    slices = self.slice_file(full_path)
                    # Use rel_path in slices
                    for s in slices:
                        s.file_path = rel_path
                        s.boundary = f"{os.path.basename(rel_path)}:L{s.line_start}-L{s.line_end}"
                    results[rel_path] = slices

        return results

    def _slice_python_ast(
        self,
        tree: ast.AST,
        source_code: str,
        file_path: str,
    ) -> List[FunctionSlice]:
        """Extracts all function and method definitions from a parsed Python AST."""
        lines = source_code.splitlines()
        filename = os.path.basename(file_path)
        slices: List[FunctionSlice] = []

        class ASTVisitor(ast.NodeVisitor):
            def __init__(self, slicer_self: "ASTSlicer"):
                self.slicer = slicer_self
                self.current_class: Optional[str] = None

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                prev_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = prev_class

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._process_func(node, is_async=False)
                # Continue visiting in case there are nested functions or classes
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._process_func(node, is_async=True)
                self.generic_visit(node)

            def _process_func(
                self,
                node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
                is_async: bool,
            ) -> None:
                start_line = node.lineno
                if self.slicer.include_decorators and node.decorator_list:
                    # Capture decorators in line boundary if present
                    start_line = min(d.lineno for d in node.decorator_list)

                end_line = getattr(node, "end_lineno", None)
                if end_line is None:
                    # Fallback for Python versions without end_lineno
                    end_line = start_line + len(node.body)

                # Clamp within line bounds
                start_line = max(1, start_line)
                end_line = min(len(lines), max(start_line, end_line))

                fn_code_lines = lines[start_line - 1 : end_line]
                fn_code = "\n".join(fn_code_lines)

                # Signature
                signature = self.slicer._extract_signature(node)

                # Argument extraction
                args_list = self.slicer._extract_arg_names(node)
                arg_count = len(args_list)

                # Docstring
                docstring = ast.get_docstring(node)

                # Cyclomatic complexity
                complexity = self.slicer.calculate_cyclomatic_complexity(node)

                # Calls made inside function
                calls = self.slicer._extract_calls(node)

                # Return annotation
                ret_annot = None
                if node.returns:
                    try:
                        ret_annot = ast.unparse(node.returns)
                    except Exception:
                        ret_annot = getattr(node.returns, "id", None)

                # Decorators
                decorators = []
                for dec in node.decorator_list:
                    try:
                        decorators.append(ast.unparse(dec))
                    except Exception:
                        if isinstance(dec, ast.Name):
                            decorators.append(dec.id)

                boundary = f"{filename}:L{start_line}-L{end_line}"

                func_slice = FunctionSlice(
                    name=node.name,
                    signature=signature,
                    file_path=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    boundary=boundary,
                    docstring=docstring,
                    cyclomatic_complexity=complexity,
                    arg_count=arg_count,
                    args=args_list,
                    lines_of_code=len(fn_code_lines),
                    code=fn_code,
                    calls=calls,
                    class_name=self.current_class,
                    is_async=is_async,
                    return_annotation=ret_annot,
                    decorators=decorators,
                )
                slices.append(func_slice)

        visitor = ASTVisitor(self)
        visitor.visit(tree)
        # Sort by starting line
        slices.sort(key=lambda s: (s.line_start, s.line_end))
        return slices

    def calculate_cyclomatic_complexity(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.AST]) -> int:
        """Calculates McCabe cyclomatic complexity for a given function AST node."""
        visitor = _CyclomaticComplexityVisitor()
        # Visit children of the function body
        body = getattr(node, "body", [node])
        for stmt in body:
            visitor.visit(stmt)
        return max(1, visitor.complexity)

    def _extract_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Extracts formatted signature e.g. '(user: str, pwd: str = None) -> bool'."""
        try:
            args_str = ast.unparse(node.args)
            ret_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            return f"({args_str}){ret_str}"
        except Exception:
            # Fallback signature construction
            args = [a.arg for a in getattr(node.args, "args", [])]
            return f"({', '.join(args)})"

    def _extract_arg_names(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extracts a flat list of argument names."""
        names: List[str] = []
        fn_args = getattr(node, "args", None)
        if not fn_args:
            return names

        # Positional-only args
        for a in getattr(fn_args, "posonlyargs", []):
            names.append(a.arg)
        # Regular args
        for a in getattr(fn_args, "args", []):
            names.append(a.arg)
        # *args
        if getattr(fn_args, "vararg", None):
            names.append(f"*{fn_args.vararg.arg}")
        # Keyword-only args
        for a in getattr(fn_args, "kwonlyargs", []):
            names.append(a.arg)
        # **kwargs
        if getattr(fn_args, "kwarg", None):
            names.append(f"**{fn_args.kwarg.arg}")

        return names

    def _extract_calls(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extracts function and method names called within this function body."""
        visitor = _FunctionCallVisitor()
        body = getattr(node, "body", [])
        for stmt in body:
            visitor.visit(stmt)
        return visitor.calls

    def _extract_python_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extracts all import and from-import statements with line numbers."""
        imports: List[Dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "type": "direct",
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "type": "from",
                    })
        return imports

    def _extract_python_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extracts class definitions, their base classes, and line numbers."""
        classes: List[Dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = []
                for b in node.bases:
                    try:
                        bases.append(ast.unparse(b))
                    except Exception:
                        if isinstance(b, ast.Name):
                            bases.append(b.id)
                methods = [
                    m.name
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                classes.append({
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno + len(node.body)),
                    "bases": bases,
                    "methods": methods,
                })
        return classes

    def _slice_fallback_regex(
        self,
        code: str,
        file_path: str,
        language: str,
        syntax_err: Optional[str] = None,
    ) -> List[FunctionSlice]:
        """Heuristic regex function slicer for non-Python or syntax-invalid files."""
        lines = code.splitlines()
        filename = os.path.basename(file_path)
        slices: List[FunctionSlice] = []

        # Common function patterns across JS, TS, C, C++, Go, and Python fallbacks
        if language == "python":
            pattern = re.compile(r"^[ \t]*(?:async[ \t]+)?def[ \t]+([a-zA-Z0-9_]+)[ \t]*\((.*?)\):", re.MULTILINE)
        else:
            pattern = re.compile(
                r"(?:function[ \t]+([a-zA-Z0-9_]+)[ \t]*\((.*?)\)|"
                r"([a-zA-Z0-9_]+)[ \t]*\((.*?)\)[ \t]*\{|"
                r"const[ \t]+([a-zA-Z0-9_]+)[ \t]*=[ \t]*(?:async[ \t]*)?\((.*?)\)[ \t]*=>)",
                re.MULTILINE,
            )

        matches = list(pattern.finditer(code))
        if not matches:
            # Fallback whole-file block if no functions detected
            total = max(1, len(lines))
            return [
                FunctionSlice(
                    name="module_root",
                    signature="()",
                    file_path=file_path,
                    line_start=1,
                    line_end=total,
                    boundary=f"{filename}:L1-L{total}",
                    docstring=None,
                    cyclomatic_complexity=1,
                    arg_count=0,
                    args=[],
                    lines_of_code=total,
                    code=code[:2000],
                    calls=[],
                )
            ]

        for i, match in enumerate(matches):
            groups = match.groups()
            name = next((g for g in groups[::2] if g), f"func_{i}")
            raw_args = next((g for g in groups[1::2] if g is not None), "")
            args_list = [a.strip().split(":")[0].strip() for a in raw_args.split(",") if a.strip()]

            start_char = match.start()
            start_line = code[:start_char].count("\n") + 1

            if i + 1 < len(matches):
                next_start = matches[i + 1].start()
                end_line = max(start_line, code[:next_start].count("\n"))
            else:
                end_line = len(lines)

            end_line = min(len(lines), max(start_line, end_line))
            fn_lines = lines[start_line - 1 : end_line]
            fn_code = "\n".join(fn_lines)

            # Heuristic complexity
            branches = len(re.findall(r"\b(if|else if|elif|for|while|case|catch|except)\b", fn_code))
            complexity = 1 + branches

            # Heuristic calls
            raw_calls = re.findall(r"\b([a-zA-Z0-9_]+)\s*\(", fn_code)
            calls = [c for c in set(raw_calls) if c != name and c not in {"if", "for", "while", "switch", "catch"}]

            boundary = f"{filename}:L{start_line}-L{end_line}"

            slices.append(
                FunctionSlice(
                    name=name,
                    signature=f"({raw_args})",
                    file_path=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    boundary=boundary,
                    docstring=None,
                    cyclomatic_complexity=complexity,
                    arg_count=len(args_list),
                    args=args_list,
                    lines_of_code=len(fn_lines),
                    code=fn_code,
                    calls=calls,
                )
            )

        return slices

    def _detect_language(self, file_path: str) -> str:
        """Determines programming language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".go": "go",
            ".java": "java",
        }
        return mapping.get(ext, "unknown")
