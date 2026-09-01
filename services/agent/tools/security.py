import os
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ToolPermission(str, Enum):
    STORAGE_READ = "storage:read"
    STORAGE_WRITE = "storage:write"
    SANDBOX_EXECUTE = "sandbox:execute"
    KNOWLEDGE_ACCESS = "knowledge:access"
    DOCUMENT_GENERATE = "document:generate"
    CALCULATOR = "calculator:eval"


class SecurityViolationError(Exception):
    """Base exception for security boundary violations."""
    pass


class PathTraversalError(SecurityViolationError):
    """Raised when an illegal directory traversal or unauthorized path is detected."""
    pass


class UnauthorizedToolAccessError(SecurityViolationError):
    """Raised when a tool is called without required permissions or with forbidden arguments."""
    pass


# Allowed directory roots for file reading/writing (whitelisted storage partitions)
ALLOWED_STORAGE_ROOTS = [
    Path("storage/uploads").resolve(),
    Path("storage/knowledge").resolve(),
    Path("storage/artifacts").resolve(),
    Path("storage/temp").resolve(),
    Path("storage").resolve(),
]


def validate_safe_storage_path(
    path_input: str,
    allowed_roots: Optional[List[Path]] = None,
    must_exist: bool = False,
    allow_creation_in: Optional[str] = None,
) -> Path:
    """Validate that a target path is strictly confined to whitelisted storage directories.

    Prevents:
    - Path traversal attacks (`../`, `..\\`, `..`)
    - Null-byte injection (`\0`, `%00`)
    - Absolute paths outside whitelisted directories (e.g. `C:\\Windows`, `/etc/passwd`, `.env`)
    """
    if not path_input or not isinstance(path_input, str):
        raise PathTraversalError("Path argument cannot be empty.")

    # 1. Check for null byte injection
    if "\0" in path_input or "%00" in path_input:
        raise PathTraversalError("Illegal null-byte sequence detected in path.")

    # 2. Check for explicit path traversal components
    parts = Path(path_input).parts
    if ".." in parts:
        raise PathTraversalError(f"Path traversal ('..') detected in path: '{path_input}'")

    roots = allowed_roots or ALLOWED_STORAGE_ROOTS

    # 3. Resolve path candidate
    p = Path(path_input)
    if not p.is_absolute():
        # If relative, resolve against workspace root or specified creation folder
        base_dir = Path(allow_creation_in).resolve() if allow_creation_in else Path("storage/temp").resolve()
        # If user passed "storage/uploads/foo.pdf", check if already contains storage
        if path_input.startswith("storage"):
            resolved = Path(path_input).resolve()
        else:
            # Check candidate storage locations
            candidate_dirs = [Path("storage/uploads"), Path("storage/knowledge"), Path("storage/artifacts"), Path("storage/temp")]
            found = None
            for cd in candidate_dirs:
                cand = (cd / p).resolve()
                if cand.exists() and cand.is_file():
                    found = cand
                    break
            resolved = found if found else (base_dir / p).resolve()
    else:
        resolved = p.resolve()

    # 4. Enforce containment within whitelisted roots
    is_whitelisted = False
    for root in roots:
        try:
            resolved.relative_to(root)
            is_whitelisted = True
            break
        except ValueError:
            continue

    if not is_whitelisted:
        raise PathTraversalError(
            f"Access denied: Path '{path_input}' is outside authorized sovereign storage directories."
        )

    # 5. Check existence if required
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Requested file not found in sovereign storage: '{path_input}'")

    return resolved
