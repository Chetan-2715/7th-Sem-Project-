"""
backend/services/ingestor.py
Codebase ingestion service:
- Shallow clones public GitHub repositories.
- Safely extracts uploaded .zip archives.
- Discovers target language source files.
- Cleans up temporary audit directories.
"""

import os
import re
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".pyw": "python",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".hxx": "cpp_header",
    ".js": "javascript",
    ".jsx": "javascript_react",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript_react",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".sh": "bash",
    ".bash": "bash",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".env": "env",
    ".toml": "toml"
}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", ".idea", ".vscode"
}


def detect_code_language(code: str, fallback_filename: str = "snippet.py") -> Tuple[str, str]:
    """
    Infers the programming language and proper extension from raw code heuristics.
    Returns: (detected_filename, language)
    """
    if not code or not code.strip():
        ext = Path(fallback_filename).suffix.lower()
        return fallback_filename, SUPPORTED_EXTENSIONS.get(ext, "python")

    text = code.strip()

    # If the user passed a specific non-default filename like "auth.go" or "main.cpp", preserve it
    user_ext = Path(fallback_filename).suffix.lower()
    if user_ext and user_ext != ".py" and user_ext in SUPPORTED_EXTENSIONS:
        return fallback_filename, SUPPORTED_EXTENSIONS[user_ext]

    # Heuristic scoring
    js_markers = [
        r"\b(?:const|let|var)\s+[a-zA-Z0-9_]+\s*=",
        r"\bfunction\s+[a-zA-Z0-9_]+\s*\(",
        r"\bconsole\.(?:log|error|warn)\b",
        r"\bdocument\.(?:getElementById|querySelector|write|createElement)\b",
        r"\bwindow\.(?:location|localStorage|sessionStorage)\b",
        r"\b(?:require\s*\(|module\.exports\b|export\s+(?:default|const|let|function))",
        r"\.innerHTML\b",
        r"\.textContent\b",
        r"=>\s*\{?",
    ]
    py_markers = [
        r"^\s*def\s+[a-zA-Z0-9_]+\s*\(.*?\)\s*:",
        r"^\s*import\s+[a-zA-Z0-9_]+",
        r"^\s*from\s+[a-zA-Z0-9_.]+\s+import\b",
        r"^\s*class\s+[a-zA-Z0-9_]+(?:\(.*?\))?\s*:",
        r"\bprint\s*\(",
        r"\belif\b",
        r"\bif\s+__name__\s*==\s*['\"]__main__['\"]:",
        r"\bself\.[a-zA-Z0-9_]+",
    ]
    c_markers = [
        r"#\s*include\s*[<\"].*?[>\"]",
        r"\bint\s+main\s*\(",
        r"\bprintf\s*\(",
        r"\bstd::[a-zA-Z0-9_]+",
        r"\bmalloc\s*\(",
        r"\bcout\s*<<",
    ]
    java_markers = [
        r"\bpublic\s+class\s+[a-zA-Z0-9_]+",
        r"\bSystem\.out\.print(?:ln)?\s*\(",
        r"\bpublic\s+static\s+void\s+main\b",
        r"\bpackage\s+[a-zA-Z0-9_.]+;",
    ]

    js_score = sum(1 for m in js_markers if re.search(m, text, re.MULTILINE))
    py_score = sum(1 for m in py_markers if re.search(m, text, re.MULTILINE))
    c_score = sum(1 for m in c_markers if re.search(m, text, re.MULTILINE))
    java_score = sum(1 for m in java_markers if re.search(m, text, re.MULTILINE))

    # Highest score wins; fallback to python if ambiguous
    scores = [
        ("javascript", ".js", js_score),
        ("python", ".py", py_score),
        ("cpp", ".cpp", c_score),
        ("java", ".java", java_score)
    ]
    scores.sort(key=lambda x: x[2], reverse=True)

    best_lang, best_ext, top_score = scores[0]
    if top_score > 0 and top_score > py_score:
        stem = Path(fallback_filename).stem
        return f"{stem}{best_ext}", best_lang
    elif py_score > 0:
        stem = Path(fallback_filename).stem
        return f"{stem}.py", "python"

    # Default to user's fallback
    ext = Path(fallback_filename).suffix.lower() or ".py"
    return fallback_filename, SUPPORTED_EXTENSIONS.get(ext, "python")


class IngestionError(Exception):
    """Custom exception raised when repository ingestion fails."""
    pass


class CodebaseIngestor:
    """Manages cloning, extracting, and indexing source files for auditing."""

    def __init__(self, base_workspace: Optional[str] = None):
        self.base_workspace = base_workspace or tempfile.gettempdir()

    def clone_github_repo(self, repo_url: str, branch: str = "main") -> Tuple[str, str]:
        """
        Shallow clones a public git repository.
        Returns: (repo_dir_path, repo_name)
        """
        if not repo_url.startswith(("http://", "https://")):
            raise IngestionError(f"Invalid repository URL: {repo_url}. Must start with http:// or https://")

        # Extract repo name from URL
        clean_url = repo_url.rstrip("/")
        repo_name = clean_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        target_dir = tempfile.mkdtemp(prefix=f"audit_{repo_name}_", dir=self.base_workspace)

        cmd = [
            "git", "clone",
            "--depth", "1",
            "--branch", branch,
            clean_url,
            target_dir
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90
            )
            # If specified branch failed, try cloning without branch flag (default branch)
            if result.returncode != 0:
                fallback_cmd = ["git", "clone", "--depth", "1", clean_url, target_dir]
                fallback_result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    timeout=90
                )
                if fallback_result.returncode != 0:
                    self.cleanup(target_dir)
                    raise IngestionError(f"Git clone failed: {fallback_result.stderr.strip()}")

            return target_dir, repo_name

        except subprocess.TimeoutExpired:
            self.cleanup(target_dir)
            raise IngestionError("Git clone timed out after 90 seconds. Repository may be too large or unreachable.")
        except Exception as e:
            self.cleanup(target_dir)
            raise IngestionError(f"Failed to clone repository: {str(e)}")

    def extract_zip(self, zip_filepath: str) -> Tuple[str, str]:
        """
        Safely extracts an uploaded zip archive.
        Mitigates Zip Slip vulnerability by validating canonical paths.
        Returns: (extracted_dir_path, archive_name)
        """
        archive_name = Path(zip_filepath).stem
        target_dir = tempfile.mkdtemp(prefix=f"audit_zip_{archive_name}_", dir=self.base_workspace)

        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zf:
                target_path = Path(target_dir).resolve()
                for member in zf.namelist():
                    member_path = (target_path / member).resolve()
                    if not str(member_path).startswith(str(target_path)):
                        raise IngestionError(f"Unsafe zip archive: path traversal detected ({member})")
                zf.extractall(target_dir)

            # If zip contained a single root directory, step into it
            entries = os.listdir(target_dir)
            if len(entries) == 1 and os.path.isdir(os.path.join(target_dir, entries[0])):
                return os.path.join(target_dir, entries[0]), archive_name

            return target_dir, archive_name

        except zipfile.BadZipFile:
            self.cleanup(target_dir)
            raise IngestionError("The uploaded file is not a valid or readable ZIP archive.")
        except Exception as e:
            self.cleanup(target_dir)
            raise IngestionError(f"Failed to extract zip archive: {str(e)}")

    def walk_codebase(self, root_dir: str) -> List[Dict[str, str]]:
        """
        Scans directory tree and collects all supported source code files.
        Returns a list of dicts: [{'path': ..., 'rel_path': ..., 'language': ..., 'content': ...}]
        """
        collected_files = []
        root_path = Path(root_dir).resolve()

        for current_root, dirs, files in os.walk(root_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

            for file in files:
                file_ext = Path(file).suffix.lower()
                if file_ext in SUPPORTED_EXTENSIONS:
                    full_path = Path(current_root) / file
                    try:
                        # Skip files larger than 1MB (e.g. minified bundles or datasets)
                        if full_path.stat().st_size > 1_000_000:
                            continue

                        rel_path = str(full_path.relative_to(root_path)).replace("\\", "/")
                        with open(full_path, "r", encoding="utf-8-sig", errors="replace") as f:
                            content = f.read().lstrip("\ufeff")

                        collected_files.append({
                            "path": str(full_path),
                            "rel_path": rel_path,
                            "filename": file,
                            "language": SUPPORTED_EXTENSIONS[file_ext],
                            "content": content,
                            "line_count": len(content.splitlines())
                        })
                    except Exception:
                        # Skip unreadable or corrupted files cleanly
                        continue

        return collected_files

    def cleanup(self, directory_path: str):
        """Removes temporary audit directory."""
        if directory_path and os.path.exists(directory_path):
            try:
                shutil.rmtree(directory_path, ignore_errors=True)
            except Exception:
                pass
