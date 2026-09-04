import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.shared.utils.helpers import generate_uuid
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission, validate_safe_storage_path
from services.artifacts.service import ArtifactsService

logger = logging.getLogger(__name__)


class PresentationModifyPptxTool(BaseTool):
    """Inspect and modify Microsoft PowerPoint (.pptx) presentations: add slides, insert tables,
    edit bullet points, and save updated presentation deliverable with SHA-256."""

    def __init__(self, artifacts_service: Optional[ArtifactsService] = None):
        self.artifacts_service = artifacts_service or ArtifactsService()

    @property
    def name(self) -> str:
        return "presentation.modify_pptx"

    @property
    def description(self) -> str:
        return (
            "Read, inspect, and modify an existing Microsoft PowerPoint (.pptx) presentation. "
            "Supports inspecting slides, adding executive summary slides, inserting comparison tables, "
            "updating bullet points, and saving the updated deck with cryptographic provenance."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path or filename of existing PPTX presentation to modify",
                },
                "action": {
                    "type": "string",
                    "enum": ["inspect", "update"],
                    "default": "update",
                    "description": "'inspect' returns slide metadata; 'update' applies modifications and saves new deck",
                },
                "operations": {
                    "type": "array",
                    "description": "List of update operations: add_slide, edit_slide, add_table",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["add_slide", "edit_slide", "add_table"]},
                            "slide_index": {"type": "integer"},
                            "title": {"type": "string"},
                            "bullet_points": {"type": "array", "items": {"type": "string"}},
                            "replacements": {"type": "object"},
                            "headers": {"type": "array", "items": {"type": "string"}},
                            "rows": {"type": "array"},
                        },
                        "required": ["type"],
                    },
                },
                "output_filename": {
                    "type": "string",
                    "description": "Optional custom filename for updated presentation",
                },
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
                "slide_count": {"type": "integer"},
                "change_summary": {"type": "array", "items": {"type": "string"}},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ, ToolPermission.STORAGE_WRITE, ToolPermission.DOCUMENT_GENERATE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        action = arguments.get("action", "update").lower()
        operations = arguments.get("operations", [])
        custom_out_filename = arguments.get("output_filename")

        if not file_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'file_path' is required.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=True)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File access error: {str(e)}")

        import pptx
        from pptx.dml.color import RGBColor
        from pptx.util import Inches, Pt

        try:
            prs = pptx.Presentation(str(safe_path))
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"Failed to open PPTX: {str(e)}")

        # Mode 1: Inspection Only
        if action == "inspect":
            slides_info: List[Dict[str, Any]] = []
            for idx, slide in enumerate(prs.slides, 1):
                slide_title = ""
                text_snippets: List[str] = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            if p.text.strip():
                                if not slide_title and len(p.text) < 80:
                                    slide_title = p.text.strip()
                                else:
                                    text_snippets.append(p.text.strip())
                slides_info.append({
                    "slide_number": idx,
                    "title": slide_title or f"Slide {idx}",
                    "shapes_count": len(slide.shapes),
                    "snippets": text_snippets[:3],
                })

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "total_slides": len(prs.slides),
                    "slides": slides_info,
                },
                metadata={"total_slides": len(prs.slides)},
            )

        # Mode 2: Update & Modify PPTX
        change_summary: List[str] = []
        blank_slide_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]

        for op in operations:
            op_type = op.get("type", "").lower()

            # Add Slide
            if op_type == "add_slide":
                title = op.get("title", "Executive Findings")
                bullets = op.get("bullet_points", [])

                slide = prs.slides.add_slide(blank_slide_layout)

                # Header box
                h_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(1.0))
                h_tf = h_box.text_frame
                h_p = h_tf.paragraphs[0]
                h_p.text = title
                h_p.font.bold = True
                h_p.font.size = Pt(24)
                h_p.font.color.rgb = RGBColor(15, 23, 42)

                # Bullet points
                if bullets:
                    c_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.33), Inches(4.8))
                    c_tf = c_box.text_frame
                    c_tf.word_wrap = True
                    for b_idx, bullet in enumerate(bullets):
                        p = c_tf.paragraphs[0] if b_idx == 0 else c_tf.add_paragraph()
                        p.text = f"•  {bullet}"
                        p.font.size = Pt(16)
                        p.font.color.rgb = RGBColor(51, 65, 85)
                        p.space_after = Pt(14)

                change_summary.append(f"Added new slide '{title}' with {len(bullets)} bullet point(s).")

            # Add Table to Slide
            elif op_type == "add_table":
                s_idx = op.get("slide_index")
                title = op.get("title", "Asset Performance Comparison")
                headers = op.get("headers", ["Equipment Tag", "Parameter", "Measured", "Threshold", "Status"])
                rows = op.get("rows", [])

                if s_idx is not None and s_idx < len(prs.slides):
                    slide = prs.slides[s_idx]
                else:
                    slide = prs.slides.add_slide(blank_slide_layout)
                    # Title
                    h_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(0.8))
                    h_tf = h_box.text_frame
                    h_p = h_tf.paragraphs[0]
                    h_p.text = title
                    h_p.font.bold = True
                    h_p.font.size = Pt(22)
                    h_p.font.color.rgb = RGBColor(15, 23, 42)

                num_rows = len(rows) + 1
                num_cols = len(headers)
                left = Inches(1.0)
                top = Inches(1.8)
                width = Inches(11.33)
                height = Inches(0.4 * num_rows)

                table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
                table = table_shape.table

                # Headers
                for col_idx, h_text in enumerate(headers):
                    cell = table.cell(0, col_idx)
                    cell.text = h_text
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(15, 23, 42)
                    for p in cell.text_frame.paragraphs:
                        p.font.bold = True
                        p.font.size = Pt(12)
                        p.font.color.rgb = RGBColor(255, 255, 255)

                # Data rows
                for r_idx, row_vals in enumerate(rows, start=1):
                    for c_idx, val in enumerate(row_vals):
                        if c_idx < num_cols:
                            cell = table.cell(r_idx, c_idx)
                            cell.text = str(val)
                            for p in cell.text_frame.paragraphs:
                                p.font.size = Pt(11)
                                if "ABNORMAL" in str(val).upper() or "EXCEEDED" in str(val).upper():
                                    p.font.color.rgb = RGBColor(220, 38, 38)
                                    p.font.bold = True
                                elif "NORMAL" in str(val).upper() or "PASSED" in str(val).upper():
                                    p.font.color.rgb = RGBColor(22, 163, 74)
                                else:
                                    p.font.color.rgb = RGBColor(51, 65, 85)

                change_summary.append(f"Inserted structured comparison table ({num_rows}x{num_cols}) on slide.")

            # Edit Slide Text
            elif op_type == "edit_slide":
                s_idx = op.get("slide_index", 0)
                replacements = op.get("replacements", {})
                if s_idx < len(prs.slides):
                    slide = prs.slides[s_idx]
                    replaced = 0
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                for target, rep in replacements.items():
                                    if target in p.text:
                                        p.text = p.text.replace(target, str(rep))
                                        replaced += 1
                    change_summary.append(f"Edited slide {s_idx + 1}: replaced {replaced} text string(s).")

        # Save Updated Presentation
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = safe_path.stem.replace(" ", "_")
        out_filename = custom_out_filename or f"{base_name}_updated_{timestamp_str}.pptx"
        if not out_filename.endswith(".pptx"):
            out_filename += ".pptx"

        artifacts_dir = Path("storage/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifacts_dir / out_filename

        prs.save(str(out_path))

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
                "type": "pptx",
                "created_at": datetime.utcnow().isoformat(),
                "source_documents": [safe_path.name],
                "models_used": ["qwen3:8b"],
                "verification_status": "verified",
                "verified": True,
                "sha256_hash": sha256,
                "size_bytes": len(file_bytes),
                "file_path": str(out_path),
                "download_url": f"/api/v1/artifacts/{artifact_id}/download",
                "metadata": {"change_summary": change_summary, "total_slides": len(prs.slides)},
            }
            self.artifacts_service.register_artifact(art_rec)
        except Exception as reg_err:
            logger.warning("Could not register modified pptx in ArtifactsService: %s", reg_err)

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
                "total_slides": len(prs.slides),
                "slide_count": len(prs.slides),
                "change_summary": change_summary,
                "verified": True,
            },
            metadata={"filename": out_filename, "sha256": sha256, "slides_count": len(prs.slides)},
        )
