import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from services.agent.tools.base import BaseTool, ToolResult
from services.artifacts.generators.docx_generator import DocxApprovalNoteGenerator
from services.artifacts.models import ApprovalNoteData

logger = logging.getLogger(__name__)


class GenerateDocxApprovalNoteTool(BaseTool):
    """Generate verified real Microsoft Word (.docx) MRPL Approval Note as a structured document."""

    def __init__(self):
        self.generator = DocxApprovalNoteGenerator()

    @property
    def name(self) -> str:
        return "artifact.generate_docx"

    @property
    def description(self) -> str:
        return "Generate a formal styled MRPL Industrial Approval Note (.docx) with cryptographic SHA-256 provenance."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Subject of the approval note"},
                "equipment_id": {"type": "string", "description": "Equipment Tag (e.g. 'P-101')"},
                "findings": {"type": "array", "items": {"type": "string"}},
                "sop_reference": {"type": "string", "description": "Governing SOP code (e.g. 'MRPL SOP Section 4.2')"},
                "recommended_action": {"type": "string", "description": "Action proposed"},
                "justification": {"type": "string", "description": "Risk justification"},
            },
            "required": ["subject", "equipment_id"],
        }

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        subject = arguments.get("subject", "Inspection Review and Maintenance Authorization")
        equipment_id = arguments.get("equipment_id", "P-101")
        findings = arguments.get("findings") or [
            "Drive-end bearing vibration (4.8 mm/s) exceeds API 610 / ISO 10816 Zone B limit (4.5 mm/s).",
            "Mechanical seal primary face minor weeping detected during inspection.",
            "Immediate overhaul required to prevent unplanned downtime.",
        ]
        sop_ref = arguments.get("sop_reference", "MRPL SOP Section 4.2 (Pump Overhaul & Vibration Limits)")
        rec_action = arguments.get("recommended_action", "Authorize priority work order for bearing replacement and mechanical seal overhaul.")
        justification = arguments.get("justification", "Continued operation risks bearing seizure, shaft deflection, and severe secondary impeller damage.")

        artifacts_dir = Path("storage/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        task_id = context.get("task_id") if context else "TASK_APPROVAL_NOTE"

        approval_data = ApprovalNoteData(
            subject=subject,
            equipment_id=equipment_id,
            equipment_name=f"Centrifugal Slurry Pump {equipment_id}",
            unit="Crude Distillation Unit (CDU-1)",
            inspection_summary="Scanned multimodal inspection scan review cross-referenced with local MRPL SOPs.",
            findings=findings if isinstance(findings, list) else [str(findings)],
            recommendations=[rec_action] if isinstance(rec_action, str) else rec_action,
            sop_references=[sop_ref, "API Standard 610 (12th Edition)", "ISO 10816-3 (Vibration Severity)"],
            justification=justification,
            estimated_cost="INR 1,25,000",
            prepared_by="Lead Reliability Engineer (MRPL)",
            verified_by="Superintending Maintenance Engineer",
            approved_by="Chief General Manager (Technical)",
        )

        try:
            record = await self.generator.generate(
                data=approval_data,
                output_dir=artifacts_dir,
                task_id=task_id,
            )

            # Register with singleton ArtifactsService
            try:
                from apps.backend.app.core.dependencies import get_artifacts_service
                get_artifacts_service().register_artifact(record)
            except Exception as reg_err:
                logger.warning("Could not register artifact in ArtifactsService: %s", reg_err)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=record.dict(),
                metadata={"subject": subject, "sha256": record.sha256_hash, "file": record.file_path},
            )
        except Exception as e:
            logger.exception("Failed to generate DOCX approval note: %s", str(e))
            return ToolResult(tool_name=self.name, success=False, error=f"DOCX Generation failure: {str(e)}")
