"""
backend/services/ingestor.py
Codebase ingestion service:
- Shallow clones public GitHub repositories.
- Safely extracts uploaded .zip archives.
- Discovers target language source files.
- Cleans up temporary audit directories.
"""

import os
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".js": "javascript",
    ".jsx": "javascript_react",
    ".ts": "typescript",
    ".tsx": "typescript_react"
}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", ".idea", ".vscode"
}


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
                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()

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
