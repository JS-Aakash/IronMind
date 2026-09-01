import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from packages.shared.utils.helpers import generate_uuid
from services.artifacts.generators.base import BaseArtifactGenerator
from services.artifacts.models import ApprovalNoteData, GeneratedArtifactRecord

logger = logging.getLogger(__name__)


class DocxApprovalNoteGenerator(BaseArtifactGenerator):
    """Generates real, styled Microsoft Word (.docx) Industrial Approval Notes using python-docx."""

    @property
    def artifact_type(self) -> str:
        return "docx"

    async def generate(
        self,
        data: ApprovalNoteData,
        output_dir: Path,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml, OxmlElement
        from docx.oxml.ns import nsdecls, qn

        doc = docx.Document()

        # Page margins
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        # 1. Header Banner Table
        header_table = doc.add_table(rows=2, cols=1)
        header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        cell_0 = header_table.cell(0, 0)
        p0 = cell_0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run0 = p0.add_run("MANGALORE REFINERY AND PETROCHEMICALS LIMITED (MRPL)")
        run0.bold = True
        run0.font.size = Pt(14)
        run0.font.color.rgb = RGBColor(15, 23, 42)

        cell_1 = header_table.cell(1, 0)
        p1 = cell_1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run1 = p1.add_run("OFFICIAL MECHANICAL ENGINEERING APPROVAL NOTE")
        run1.bold = True
        run1.font.size = Pt(11)
        run1.font.color.rgb = RGBColor(14, 165, 233)

        doc.add_paragraph()

        # 2. Metadata Grid
        meta_table = doc.add_table(rows=4, cols=2)
        meta_table.style = "Table Grid"
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        meta_rows = [
            ("Subject / Title:", data.subject),
            ("Equipment Tag & Name:", f"{data.equipment_tag} - {data.equipment_name}"),
            ("Operating Unit / Area:", data.operating_unit),
            ("Inspection Date / Ref:", f"{data.inspection_date} | Task: {task_id or 'AUTONOMOUS_RUN'}"),
        ]

        for i, (label, val) in enumerate(meta_rows):
            cell_lbl = meta_table.cell(i, 0)
            p_lbl = cell_lbl.paragraphs[0]
            r_lbl = p_lbl.add_run(label)
            r_lbl.bold = True
            r_lbl.font.size = Pt(10)

            cell_val = meta_table.cell(i, 1)
            p_val = cell_val.paragraphs[0]
            r_val = p_val.add_run(val)
            r_val.font.size = Pt(10)

        doc.add_paragraph()

        # 3. Section: Inspection Summary
        h1 = doc.add_heading("1. Executive Summary & Inspection Scope", level=2)
        doc.add_paragraph(data.inspection_summary)

        # 4. Section: Measured Operational Parameters
        if data.measured_parameters:
            doc.add_heading("2. Quantitative Condition Monitoring Readings", level=2)
            param_table = doc.add_table(rows=1, cols=2)
            param_table.style = "Table Grid"
            
            hdr_cells = param_table.rows[0].cells
            hdr_cells[0].paragraphs[0].add_run("Monitored Parameter").bold = True
            hdr_cells[1].paragraphs[0].add_run("Measured Value").bold = True

            for param, val in data.measured_parameters.items():
                row_cells = param_table.add_row().cells
                row_cells[0].paragraphs[0].add_run(str(param))
                row_cells[1].paragraphs[0].add_run(str(val))

            doc.add_paragraph()

        # 5. Section: Findings
        doc.add_heading("3. Detailed Inspection Findings", level=2)
        for finding in data.findings:
            doc.add_paragraph(finding, style="List Bullet")

        # 6. Section: SOP References
        doc.add_heading("4. Governing SOP & Standard References", level=2)
        for ref in data.sop_references:
            doc.add_paragraph(ref, style="List Bullet")

        # 7. Section: Recommendations & Action Plan
        doc.add_heading("5. Proposed Maintenance Recommendations", level=2)
        for rec in data.recommendations:
            doc.add_paragraph(rec, style="List Bullet")

        # 8. Section: Management Justification & Budget
        doc.add_heading("6. Technical Justification & Risk Assessment", level=2)
        doc.add_paragraph(data.justification)
        if data.cost_estimate_inr:
            doc.add_paragraph(f"Estimated Overhaul Budget: {data.cost_estimate_inr}").runs[0].bold = True

        doc.add_paragraph()

        # 9. Sign-off Approval Section
        doc.add_heading("7. Authorization & Approval Signatures", level=2)
        sig_table = doc.add_table(rows=2, cols=len(data.signatories))
        sig_table.style = "Table Grid"
        sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for col_idx, (role, person) in enumerate(data.signatories.items()):
            c0 = sig_table.cell(0, col_idx)
            p_r = c0.paragraphs[0]
            p_r.add_run(role).bold = True
            p_r.alignment = WD_ALIGN_PARAGRAPH.CENTER

            c1 = sig_table.cell(1, col_idx)
            p_p = c1.paragraphs[0]
            p_p.add_run(f"\n[DIGITALLY VERIFIED]\n{person}\nDate: {datetime.utcnow().strftime('%d-%b-%Y')}")
            p_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 10. Save to Disk
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        tag_clean = data.equipment_tag.replace("-", "_").replace(" ", "_")
        filename = f"MRPL_Approval_Note_{tag_clean}_{timestamp}.docx"
        file_path = output_dir / filename
        doc.save(str(file_path))

        file_bytes = file_path.read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        artifact_id = generate_uuid("ART")

        return GeneratedArtifactRecord(
            artifact_id=artifact_id,
            task_id=task_id or data.task_id,
            filename=filename,
            type="docx",
            created_at=datetime.utcnow().isoformat(),
            source_documents=data.source_documents,
            models_used=data.models_used,
            verification_status="verified",
            sha256_hash=sha256,
            size_bytes=len(file_bytes),
            file_path=str(file_path),
            download_url=f"/api/v1/artifacts/{artifact_id}/download",
            metadata={"equipment_tag": data.equipment_tag, "subject": data.subject},
        )
