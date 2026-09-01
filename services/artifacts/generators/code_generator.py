import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from packages.shared.utils.helpers import generate_uuid
from services.artifacts.generators.base import BaseArtifactGenerator
from services.artifacts.models import GeneratedArtifactRecord

logger = logging.getLogger(__name__)


class SourceCodeArtifactData(BaseModel):
    filename: str = Field(default="calculate_pump_efficiency.py")
    code: str
    language: str = Field(default="python")
    task_id: Optional[str] = None
    source_documents: List[str] = Field(default_factory=list)
    models_used: List[str] = Field(default_factory=lambda: ["qwen2.5-coder:7b"])
    verification_status: str = "verified"


class SourceCodeArtifactGenerator(BaseArtifactGenerator):
    """Generates source code and script business deliverables."""

    @property
    def artifact_type(self) -> str:
        return "code"

    async def generate(
        self,
        data: SourceCodeArtifactData,
        output_dir: Path,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        stem = Path(data.filename).stem
        ext = Path(data.filename).suffix or ".py"
        filename = f"{stem}_{timestamp}{ext}"
        file_path = output_dir / filename

        file_path.write_text(data.code, encoding="utf-8")

        file_bytes = file_path.read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        artifact_id = generate_uuid("ART")

        return GeneratedArtifactRecord(
            artifact_id=artifact_id,
            task_id=task_id or data.task_id,
            filename=filename,
            type="python" if ext == ".py" else ext.lstrip("."),
            created_at=datetime.utcnow().isoformat(),
            source_documents=data.source_documents,
            models_used=data.models_used,
            verification_status=data.verification_status,
            sha256_hash=sha256,
            size_bytes=len(file_bytes),
            file_path=str(file_path),
            download_url=f"/api/v1/artifacts/{artifact_id}/download",
            metadata={"language": data.language, "lines_of_code": len(data.code.splitlines())},
        )
