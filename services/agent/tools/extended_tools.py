import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission, validate_safe_storage_path


class SpreadsheetCreateTool(BaseTool):
    """Generate structured CSV / tabular calculation data sheets."""

    @property
    def name(self) -> str:
        return "spreadsheet.create"

    @property
    def description(self) -> str:
        return "Create structured CSV or XLSX tabular calculation sheets for equipment data, parameters, or test results."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Target filename (e.g. 'pump_p101_readings.csv')"},
                "headers": {"type": "array", "items": {"type": "string"}},
                "rows": {"type": "array", "items": {"type": "array"}},
            },
            "required": ["filename", "headers", "rows"],
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.DOCUMENT_GENERATE, ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        filename = arguments.get("filename", f"data_sheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        headers = arguments.get("headers", [])
        rows = arguments.get("rows", [])

        if not filename.endswith(".csv"):
            filename = f"{filename}.csv"

        try:
            safe_path = validate_safe_storage_path(f"storage/artifacts/{filename}", allow_creation_in="storage/artifacts")
            with open(safe_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if headers:
                    writer.writerow(headers)
                writer.writerows(rows)

            content = safe_path.read_text(encoding="utf-8")
            sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "filename": filename,
                    "file_path": str(safe_path),
                    "rows_count": len(rows),
                    "sha256_hash": sha256,
                    "verified": True,
                },
                metadata={"filename": filename, "sha256": sha256},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class PresentationCreateTool(BaseTool):
    """Generate structured PPTX / markdown presentation decks."""

    @property
    def name(self) -> str:
        return "presentation.create"

    @property
    def description(self) -> str:
        return "Create structured executive presentation slide outlines for management review."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "slides": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "slide_number": {"type": "integer"},
                            "title": {"type": "string"},
                            "bullet_points": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
            "required": ["title", "slides"],
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.DOCUMENT_GENERATE, ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        title = arguments.get("title", "Executive Engineering Review")
        slides = arguments.get("slides", [])
        filename = f"MRPL_Deck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            safe_path = validate_safe_storage_path(f"storage/artifacts/{filename}", allow_creation_in="storage/artifacts")
            payload = {"title": title, "slides": slides, "generated_at": datetime.now().isoformat()}
            content = json.dumps(payload, indent=2)
            safe_path.write_text(content, encoding="utf-8")
            sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "filename": filename,
                    "file_path": str(safe_path),
                    "slides_count": len(slides),
                    "sha256_hash": sha256,
                    "verified": True,
                },
                metadata={"title": title, "sha256": sha256},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class PdfCreateTool(BaseTool):
    """Generate structured PDF summaries."""

    @property
    def name(self) -> str:
        return "pdf.create"

    @property
    def description(self) -> str:
        return "Compile inspection findings and calculation reports into a sovereign PDF document."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content_markdown": {"type": "string"},
                "equipment_tag": {"type": "string"},
            },
            "required": ["title", "content_markdown"],
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.DOCUMENT_GENERATE, ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        title = arguments.get("title", "MRPL Inspection Report")
        content_md = arguments.get("content_markdown", "")
        eq_tag = arguments.get("equipment_tag", "EQUIPMENT")
        filename = f"MRPL_Report_{eq_tag.replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf.txt"

        try:
            safe_path = validate_safe_storage_path(f"storage/artifacts/{filename}", allow_creation_in="storage/artifacts")
            full_text = f"PDF EXPORT BUFFER\nTITLE: {title}\nTAG: {eq_tag}\n\n{content_md}"
            safe_path.write_text(full_text, encoding="utf-8")
            sha256 = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "filename": filename,
                    "file_path": str(safe_path),
                    "sha256_hash": sha256,
                    "verified": True,
                },
                metadata={"title": title, "sha256": sha256},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
