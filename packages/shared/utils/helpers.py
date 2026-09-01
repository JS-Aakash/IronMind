import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Union


def generate_uuid(prefix: str = "") -> str:
    """Generate a unique ID with an optional prefix."""
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}_{uid}" if prefix else uid


def calculate_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file for cryptographic provenance verification."""
    sha256 = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        return ""
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_current_utc_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()
