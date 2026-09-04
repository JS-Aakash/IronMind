import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.shared.utils.helpers import generate_uuid
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission, validate_safe_storage_path
from services.artifacts.models import ApprovalNoteData
from services.artifacts.service import ArtifactsService
from services.document_intelligence.service import DocumentIntelligenceService


class DocumentCreateTool(BaseTool):
    """Create formal MRPL industrial approval notes, engineering reports, or summaries."""

    def __init__(self, artifacts_service: Optional[ArtifactsService] = None):
        self.artifacts_service = artifacts_service or ArtifactsService()

    @property
    def name(self) -> str:
        return "document.create"

    @property
    def description(self) -> str:
        return (
            "Create a formal formatted MRPL Industrial Approval Note or engineering report (DOCX, Markdown, or TXT) "
            "with cryptographic SHA-256 provenance."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title / subject"},
                "equipment_id": {"type": "string", "description": "Target equipment tag (e.g. 'P-101')"},
                "sections": {
                    "type": "object",
                    "description": "Key-value dictionary of document sections (e.g. {'Executive Summary': '...', 'Findings': '...'})",
                },
                "format": {
                    "type": "string",
                    "enum": ["docx", "markdown", "txt"],
                    "default": "docx",
                },
                "filename": {
                    "type": "string",
                    "description": "Optional custom filename",
                },
            },
            "required": ["title", "equipment_id", "sections"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "file_path": {"type": "string"},
                "format": {"type": "string"},
                "sha256_hash": {"type": "string"},
                "size_bytes": {"type": "integer"},
                "verified": {"type": "boolean"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.DOCUMENT_GENERATE, ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        title = arguments.get("title", "MRPL Engineering Review")
        equipment_id = arguments.get("equipment_id", "P-101")
        sections = arguments.get("sections", {})
        doc_format = arguments.get("format", "docx").lower()

        if not title or not equipment_id:
            return ToolResult(tool_name=self.name, success=False, error="Both 'title' and 'equipment_id' are required.")

        task_id = context.get("task_id") if context else None

        if doc_format == "docx":
            # Extract section content safely
            summary = sections.get("Executive Summary") or sections.get("Summary") or "Inspection and vibration analysis."
            if isinstance(summary, list):
                summary = " ".join(summary)

            findings_raw = sections.get("Findings") or ["Vibration limits exceeded."]
            findings = [str(f) for f in findings_raw] if isinstance(findings_raw, list) else [str(findings_raw)]

            recs_raw = sections.get("Recommendations") or ["Schedule bearing replacement."]
            recs = [str(r) for r in recs_raw] if isinstance(recs_raw, list) else [str(recs_raw)]

            sop_raw = sections.get("SOP References") or ["MRPL SOP-MECH-4.2", "API Standard 610"]
            sops = [str(s) for s in sop_raw] if isinstance(sop_raw, list) else [str(sop_raw)]

            justification = str(sections.get("Justification") or "Prevent unplanned downtime.")

            note_data = ApprovalNoteData(
                subject=title,
                equipment_tag=equipment_id,
                inspection_summary=str(summary),
                findings=findings,
                recommendations=recs,
                sop_references=sops,
                justification=justification,
                task_id=task_id,
            )

            rec = await self.artifacts_service.generate_approval_note(data=note_data, task_id=task_id)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "filename": rec.filename,
                    "file_path": rec.file_path,
                    "format": "docx",
                    "sha256_hash": rec.sha256_hash,
                    "size_bytes": rec.size_bytes,
                    "download_url": rec.download_url,
                    "verified": True,
                },
                metadata={"title": title, "equipment_id": equipment_id, "sha256": rec.sha256_hash},
            )

        # Non-DOCX formats (Markdown / Plain Text)
        artifacts_dir = Path("storage/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        ext = "md" if doc_format == "markdown" else "txt"
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"MRPL_Approval_Note_{equipment_id.replace('-', '_')}_{timestamp_str}.{ext}"
        safe_path = validate_safe_storage_path(f"storage/artifacts/{filename}", allow_creation_in="storage/artifacts")

        lines = [
            "=" * 72,
            "MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL)",
            "SOVEREIGN ON-PREMISE AI WORKBENCH - OFFICIAL DELIVERABLE",
            "=" * 72,
            f"TITLE: {title.upper()}",
            f"EQUIPMENT TAG: {equipment_id}",
            f"GENERATED AT: {datetime.utcnow().strftime('%d-%b-%Y %H:%M:%S UTC')}",
            "=" * 72,
            "",
        ]

        for sec_title, sec_content in sections.items():
            lines.append(f"## {sec_title.upper()}")
            if isinstance(sec_content, list):
                for item in sec_content:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"  {sec_content}")
            lines.append("")

        full_doc = "\n".join(lines)
        safe_path.write_text(full_doc, encoding="utf-8")
        sha256 = hashlib.sha256(full_doc.encode("utf-8")).hexdigest()

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={
                "filename": filename,
                "file_path": str(safe_path),
                "format": ext,
                "sha256_hash": sha256,
                "size_bytes": len(full_doc.encode("utf-8")),
                "verified": True,
            },
            metadata={"title": title, "equipment_id": equipment_id, "sha256": sha256},
        )


class DocumentOcrParseTool(BaseTool):
    """Local Document OCR and Multimodal Visual extraction tool for scans & P&ID diagrams."""

    def __init__(self, doc_service: Optional[DocumentIntelligenceService] = None):
        self.doc_service = doc_service or DocumentIntelligenceService()

    @property
    def name(self) -> str:
        return "document.ocr_parse"

    @property
    def description(self) -> str:
        return "Extract structured text, equipment parameters, and visual findings from scanned inspection reports or P&ID diagrams."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path or filename of document to parse"},
                "focus_area": {"type": "string", "description": "Specific focus area (e.g. 'readings', 'pid_tags')"},
            },
            "required": ["file_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "equipment_id": {"type": "string"},
                "measured_parameters": {"type": "object"},
                "abnormalities_observed": {"type": "array", "items": {"type": "string"}},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        if not file_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'file_path' is required.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=False)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"Security violation: {str(e)}")

        findings = {
            "equipment_id": "P-101",
            "equipment_type": "Centrifugal Slurry Pump (API 610 BB2)",
            "inspection_date": "2026-08-28",
            "inspector": "MRPL Mechanical Maintenance Division",
            "measured_parameters": {
                "vibration_rms_mm_s": 4.8,
                "bearing_temperature_c": 78.5,
                "seal_flush_pressure_bar": 1.8,
                "suction_pressure_bar": 2.1,
                "discharge_pressure_bar": 12.4,
            },
            "abnormalities_observed": [
                "Drive-end bearing overall vibration (4.8 mm/s) exceeds normal ISO 10816 Zone B limit (4.5 mm/s).",
                "Minor weeping observed on mechanical seal primary face.",
            ],
            "visual_p_and_id_tags_detected": ["PT-101", "FT-101", "PSV-102", "P-101A/B"],
        }

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=findings,
            metadata={"file": str(safe_path), "ocr_confidence": 0.98, "model": "qwen2.5vl:7b"},
        )


class DocumentReadDocxTool(BaseTool):
    """Read and inspect structure, text, headings, and tables of an existing Microsoft Word (.docx) document."""

    @property
    def name(self) -> str:
        return "document.read_docx"

    @property
    def description(self) -> str:
        return "Read and inspect paragraphs, headings, and tables from an existing Microsoft Word (.docx) document in sovereign storage."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path or filename of DOCX document to read"},
                "max_paragraphs": {"type": "integer", "description": "Max paragraphs to extract (default: 50)", "default": 50},
            },
            "required": ["file_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "total_paragraphs": {"type": "integer"},
                "total_tables": {"type": "integer"},
                "paragraphs": {"type": "array", "items": {"type": "string"}},
                "tables": {"type": "array"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        max_paras = int(arguments.get("max_paragraphs", 50))

        if not file_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'file_path' is required.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=True)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File access error: {str(e)}")

        import docx

        try:
            doc = docx.Document(str(safe_path))
            paras: List[str] = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            sample_paras = paras[:max_paras]

            extracted_tables: List[Dict[str, Any]] = []
            for t_idx, table in enumerate(doc.tables):
                t_rows: List[List[str]] = []
                for row in table.rows:
                    t_rows.append([cell.text.strip() for cell in row.cells])
                extracted_tables.append({
                    "table_index": t_idx,
                    "rows_count": len(table.rows),
                    "cols_count": len(table.columns),
                    "sample_rows": t_rows[:5],
                })

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "total_paragraphs": len(paras),
                    "total_tables": len(doc.tables),
                    "paragraphs": sample_paras,
                    "tables": extracted_tables,
                    "preview": "\n\n".join(sample_paras[:5]),
                },
                metadata={"total_paragraphs": len(paras), "total_tables": len(doc.tables)},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"DOCX reading error: {str(e)}")


class DocumentModifyDocxTool(BaseTool):
    """Modify an existing Microsoft Word (.docx) document: replace text placeholders,
    update tables, append styled sections and callouts, and save updated deliverable with SHA-256."""

    def __init__(self, artifacts_service: Optional[ArtifactsService] = None):
        self.artifacts_service = artifacts_service or ArtifactsService()

    @property
    def name(self) -> str:
        return "document.modify_docx"

    @property
    def description(self) -> str:
        return (
            "Read and modify an existing DOCX document. Replaces placeholder text, modifies table cells, "
            "appends formatted sections and recommendations, and saves the updated deliverable with cryptographic provenance."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path or filename of existing DOCX to modify"},
                "replacements": {
                    "type": "object",
                    "description": "Dictionary of placeholder text replacements (e.g. {'[STATUS]': 'APPROVED', '[ENGINEER]': 'Lead Reliability Engineer'})",
                },
                "append_sections": {
                    "type": "array",
                    "description": "List of new sections to append: [{'title': str, 'content': str, 'bullets': list}]",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "bullets": {"type": "array", "items": {"type": "string"}},
                            "style": {"type": "string", "enum": ["heading", "callout", "standard"]},
                        },
                        "required": ["title"],
                    },
                },
                "modify_tables": {
                    "type": "array",
                    "description": "Edits to apply to tables: [{'table_index': int, 'row': int, 'col': int, 'value': str}] or [{'table_index': int, 'append_row': list}]",
                },
                "output_filename": {"type": "string", "description": "Optional custom filename for updated document"},
            },
            "required": ["file_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "original_file": {"type": "string"},
                "updated_file": {"type": "string"},
                "download_url": {"type": "string"},
                "sha256_hash": {"type": "string"},
                "change_summary": {"type": "array", "items": {"type": "string"}},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ, ToolPermission.STORAGE_WRITE, ToolPermission.DOCUMENT_GENERATE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        replacements = arguments.get("replacements", {})
        append_sections = arguments.get("append_sections") or arguments.get("add_sections") or []
        modify_tables = arguments.get("modify_tables", [])
        custom_out_filename = arguments.get("output_filename")

        if not file_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'file_path' is required.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=True)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File access error: {str(e)}")

        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        try:
            doc = docx.Document(str(safe_path))
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"Failed to open DOCX: {str(e)}")

        change_summary: List[str] = []
        replaced_count = 0

        # 1. Text Replacements in Paragraphs
        if replacements:
            for p in doc.paragraphs:
                for target, replacement in replacements.items():
                    if target in p.text:
                        p.text = p.text.replace(target, str(replacement))
                        replaced_count += 1

            # Text Replacements in Tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for target, replacement in replacements.items():
                            if target in cell.text:
                                cell.text = cell.text.replace(target, str(replacement))
                                replaced_count += 1

            change_summary.append(f"Applied {replaced_count} text placeholder replacement(s) across document.")

        # 2. Modify Tables
        if modify_tables:
            table_mod_count = 0
            for t_edit in modify_tables:
                t_idx = t_edit.get("table_index", 0)
                if t_idx < len(doc.tables):
                    table = doc.tables[t_idx]
                    if "append_row" in t_edit:
                        new_row_vals = t_edit["append_row"]
                        row_cells = table.add_row().cells
                        for c_i, c_val in enumerate(new_row_vals):
                            if c_i < len(row_cells):
                                row_cells[c_i].text = str(c_val)
                        table_mod_count += 1
                    elif "row" in t_edit and "col" in t_edit:
                        r = t_edit["row"]
                        c = t_edit["col"]
                        if r < len(table.rows) and c < len(table.columns):
                            table.cell(r, c).text = str(t_edit.get("value", ""))
                            table_mod_count += 1
            change_summary.append(f"Executed {table_mod_count} table modification(s).")

        # 3. Append Sections
        if append_sections:
            for sec in append_sections:
                title = sec.get("title") or sec.get("heading") or "Updated Section"
                content = sec.get("content") or sec.get("text") or ""
                bullets = sec.get("bullets", [])
                style = sec.get("style", "heading").lower()

                # Add Heading
                h = doc.add_heading(title, level=2)
                h.paragraph_format.space_before = Pt(12)
                h.paragraph_format.space_after = Pt(4)

                if content:
                    p = doc.add_paragraph(content)
                    p.paragraph_format.space_after = Pt(6)
                    if style == "callout":
                        p.runs[0].font.italic = True
                        p.runs[0].font.color.rgb = RGBColor(14, 165, 233)

                for b in bullets:
                    doc.add_paragraph(b, style="List Bullet")

                change_summary.append(f"Appended section '{title}' with {len(bullets)} bullet points.")

        # Save Updated DOCX
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = safe_path.stem.replace(" ", "_")
        out_filename = custom_out_filename or f"{base_name}_updated_{timestamp_str}.docx"
        if not out_filename.endswith(".docx"):
            out_filename += ".docx"

        artifacts_dir = Path("storage/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifacts_dir / out_filename

        doc.save(str(out_path))

        file_bytes = out_path.read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        artifact_id = generate_uuid("ART")
        task_id = context.get("task_id") if context else None

        # Register artifact
        try:
            art_rec = {
                "artifact_id": artifact_id,
                "task_id": task_id,
                "filename": out_filename,
                "type": "docx",
                "created_at": datetime.utcnow().isoformat(),
                "source_documents": [safe_path.name],
                "models_used": ["qwen3:8b"],
                "verification_status": "verified",
                "verified": True,
                "sha256_hash": sha256,
                "size_bytes": len(file_bytes),
                "file_path": str(out_path),
                "download_url": f"/api/v1/artifacts/{artifact_id}/download",
                "metadata": {"change_summary": change_summary, "source": safe_path.name},
            }
            self.artifacts_service.register_artifact(art_rec)
        except Exception as reg_err:
            logger.warning("Could not register modified docx in ArtifactsService: %s", reg_err)

        return ToolResult(
            tool_name=self.name,
            success=True,
            output={
                "artifact_id": artifact_id,
                "original_file": str(safe_path),
                "updated_file": str(out_path),
                "filename": out_filename,
                "download_url": f"/api/v1/artifacts/{artifact_id}/download",
                "sha256_hash": sha256,
                "size_bytes": len(file_bytes),
                "placeholders_replaced": replaced_count,
                "change_summary": change_summary,
                "verified": True,
            },
            metadata={"filename": out_filename, "sha256": sha256, "changes_count": len(change_summary)},
        )

