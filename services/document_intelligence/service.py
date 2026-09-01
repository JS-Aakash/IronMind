import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from services.document_intelligence.models import NormalizedDocument
from services.document_intelligence.pipeline import DocumentIntelligencePipeline
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class DocumentIntelligenceService:
    """Sovereign on-premise Document Intelligence Service for parsing PDFs, images, P&ID diagrams, and inspection reports."""

    def __init__(
        self,
        upload_dir: str = "storage/uploads",
        processed_dir: str = "storage/uploads/processed",
        sovereignty_service: Optional[SovereigntyService] = None,
    ):
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.sovereignty_service = sovereignty_service or SovereigntyService()
        self.pipeline = DocumentIntelligencePipeline(
            output_dir=str(self.processed_dir),
            sovereignty_service=self.sovereignty_service,
        )

    def analyze_document_structure(self, file_path: str) -> Dict[str, Any]:
        """Inspect structural properties of a file without full pipeline execution."""
        path = Path(file_path)
        return {
            "filename": path.name,
            "exists": path.exists(),
            "extension": path.suffix.lower(),
            "is_multimodal": path.suffix.lower() in [".png", ".jpg", ".jpeg", ".pdf", ".tif"],
            "status": "ready_for_local_ocr_and_vision",
        }

    async def process_document(
        self,
        file_input: Union[bytes, Path, str],
        filename: Optional[str] = None,
        enable_vision_llm: bool = True,
    ) -> NormalizedDocument:
        """Run the full Document Intelligence Pipeline on the target document."""
        return await self.pipeline.process_document(
            file_input=file_input,
            filename=filename,
            enable_vision_llm=enable_vision_llm,
        )

    def get_document(self, document_id: str) -> Optional[NormalizedDocument]:
        """Retrieve a stored processed document from local storage."""
        target_file = self.processed_dir / f"{document_id}.json"
        if not target_file.exists():
            return None
        try:
            data = json.loads(target_file.read_text(encoding="utf-8"))
            return NormalizedDocument(**data)
        except Exception as e:
            logger.error("Failed to load processed document '%s': %s", document_id, str(e))
            return None

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all processed normalized documents."""
        docs: List[Dict[str, Any]] = []
        for json_file in self.processed_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                docs.append({
                    "document_id": data.get("document_id"),
                    "filename": data.get("filename"),
                    "file_type": data.get("file_type"),
                    "total_pages": data.get("total_pages"),
                    "extracted_equipment_tags": data.get("extracted_equipment_tags", []),
                    "created_at": data.get("created_at"),
                })
            except Exception:
                continue
        return docs
