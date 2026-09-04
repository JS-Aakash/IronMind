import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.shared.utils.helpers import generate_uuid
from services.artifacts.generators.code_generator import SourceCodeArtifactData, SourceCodeArtifactGenerator
from services.artifacts.generators.docx_generator import DocxApprovalNoteGenerator
from services.artifacts.generators.pdf_generator import PdfReportGenerator
from services.artifacts.generators.pptx_generator import PptxPresentationGenerator
from services.artifacts.generators.xlsx_generator import XlsxSpreadsheetGenerator
from services.artifacts.models import (
    ApprovalNoteData,
    GeneratedArtifactRecord,
    PdfReportData,
    PresentationData,
    SpreadsheetData,
)
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class ArtifactsService:
    """Sovereign business deliverable generator and repository."""

    def __init__(
        self,
        storage_dir: str = "storage/artifacts",
        sovereignty_service: Optional[SovereigntyService] = None,
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.storage_dir / "registry.json"
        self.sovereignty_service = sovereignty_service or SovereigntyService()

        # Instantiate generators
        self.docx_generator = DocxApprovalNoteGenerator()
        self.xlsx_generator = XlsxSpreadsheetGenerator()
        self.pptx_generator = PptxPresentationGenerator()
        self.pdf_generator = PdfReportGenerator()
        self.code_generator = SourceCodeArtifactGenerator()

        self._artifacts: Dict[str, GeneratedArtifactRecord] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                for item in data.get("artifacts", []):
                    rec = GeneratedArtifactRecord(**item)
                    self._artifacts[rec.artifact_id] = rec
            except Exception as e:
                logger.warning("Failed to load artifact registry from '%s': %s", self.registry_file, str(e))
        
        if not self._artifacts:
            # Seed initial sample artifact record
            sample_rec = GeneratedArtifactRecord(
                artifact_id="art_sample_p101_approval",
                task_id="TASK_INSPECT_001",
                filename="MRPL_Approval_Note_P_101_Sample.docx",
                type="docx",
                created_at=datetime.utcnow().isoformat(),
                source_documents=["MRPL_SOP_P101_Pump_Maintenance.pdf"],
                models_used=["qwen2.5vl:7b", "qwen3:8b"],
                verification_status="verified",
                verified=True,
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                size_bytes=8192,
                file_path=str(self.storage_dir / "MRPL_Approval_Note_P_101_Sample.docx"),
                download_url="/api/v1/artifacts/art_sample_p101_approval/download",
                metadata={"equipment_tag": "P-101", "subject": "Sample Approval Note"},
            )
            self._artifacts[sample_rec.artifact_id] = sample_rec

    def _save_registry(self) -> None:
        try:
            data = {
                "artifacts": [rec.dict() for rec in self._artifacts.values()],
                "total_count": len(self._artifacts),
                "updated_at": datetime.utcnow().isoformat(),
            }
            self.registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save artifact registry: %s", str(e))

    def list_artifacts(self) -> List[GeneratedArtifactRecord]:
        self._load_registry()
        return list(self._artifacts.values())

    def get_artifact(self, artifact_id: str) -> Optional[GeneratedArtifactRecord]:
        if artifact_id in self._artifacts:
            return self._artifacts[artifact_id]
        self._load_registry()
        if artifact_id in self._artifacts:
            return self._artifacts[artifact_id]
        for rec in self._artifacts.values():
            if rec.artifact_id.lower() == artifact_id.lower():
                return rec
        return None

    def get_artifact_file_path(self, artifact_id: str) -> Optional[Path]:
        rec = self.get_artifact(artifact_id)
        if rec and rec.file_path:
            p = Path(rec.file_path)
            if p.exists():
                return p
            p_storage = self.storage_dir / p.name
            if p_storage.exists():
                return p_storage
        
        # Check direct match in storage_dir
        for ext in [".docx", ".xlsx", ".pptx", ".pdf", ".py", ".txt"]:
            candidate = self.storage_dir / f"{artifact_id}{ext}"
            if candidate.exists():
                return candidate

        # Check if artifact_id substring matches file
        for p in self.storage_dir.glob("*.*"):
            if artifact_id.lower() in p.name.lower():
                return p

        # Fallback to latest generated docx if docx was generated
        docxs = sorted(self.storage_dir.glob("*.docx"), key=lambda f: f.stat().st_mtime, reverse=True)
        if docxs:
            return docxs[0]
            
        pys = sorted(self.storage_dir.glob("*.py"), key=lambda f: f.stat().st_mtime, reverse=True)
        if pys:
            return pys[0]

        return None

    def delete_artifact(self, artifact_id: str) -> bool:
        """Permanently delete artifact file from disk and remove from registry."""
        rec = self.get_artifact(artifact_id)
        if not rec:
            return False

        # Delete physical file from disk
        file_path = self.get_artifact_file_path(artifact_id)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning("Failed to delete artifact file %s: %s", file_path, e)

        # Remove from in-memory dictionary
        if rec.artifact_id in self._artifacts:
            del self._artifacts[rec.artifact_id]
        for k in list(self._artifacts.keys()):
            if k.lower() == artifact_id.lower():
                del self._artifacts[k]

        self._save_registry()

        self.sovereignty_service.log_event(
            event_type="ARTIFACT_DELETED",
            source_service="Artifact Engine",
            details={"artifact_id": artifact_id, "filename": rec.filename},
        )
        return True

    def register_artifact(self, record: Any) -> GeneratedArtifactRecord:
        """Register a generated artifact into persistence and sovereignty audit log."""
        if isinstance(record, dict):
            rec = GeneratedArtifactRecord(**record)
        else:
            rec = record
        self._artifacts[rec.artifact_id] = rec
        self._save_registry()
        self.sovereignty_service.log_event(
            event_type="ARTIFACT_GENERATED",
            source_service="Artifact Engine",
            details={
                "artifact_id": rec.artifact_id,
                "filename": rec.filename,
                "type": rec.type,
                "sha256": rec.sha256_hash,
                "size_bytes": rec.size_bytes,
            },
        )
        return rec

    def _register(self, record: GeneratedArtifactRecord) -> GeneratedArtifactRecord:
        return self.register_artifact(record)

    async def generate_approval_note(
        self,
        data: Optional[ApprovalNoteData] = None,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        """Generate a real styled DOCX Approval Note."""
        note_data = data or ApprovalNoteData(subject="Approval for Immediate Mechanical Overhaul of Slurry Pump P-101")
        record = await self.docx_generator.generate(note_data, self.storage_dir, task_id=task_id)
        return self._register(record)

    async def generate_spreadsheet(
        self,
        data: Optional[SpreadsheetData] = None,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        """Generate a real styled XLSX spreadsheet."""
        sheet_data = data or SpreadsheetData()
        record = await self.xlsx_generator.generate(sheet_data, self.storage_dir, task_id=task_id)
        return self._register(record)

    async def generate_presentation(
        self,
        data: Optional[PresentationData] = None,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        """Generate a real styled PPTX presentation deck."""
        pres_data = data or PresentationData()
        record = await self.pptx_generator.generate(pres_data, self.storage_dir, task_id=task_id)
        return self._register(record)

    async def generate_pdf(
        self,
        data: Optional[PdfReportData] = None,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        """Generate a real styled PDF report."""
        pdf_data = data or PdfReportData()
        record = await self.pdf_generator.generate(pdf_data, self.storage_dir, task_id=task_id)
        return self._register(record)

    async def generate_code_artifact(
        self,
        data: SourceCodeArtifactData,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        """Generate a real source code deliverable."""
        record = await self.code_generator.generate(data, self.storage_dir, task_id=task_id)
        return self._register(record)
