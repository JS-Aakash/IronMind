import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from packages.shared.utils.helpers import generate_uuid
from services.artifacts.generators.base import BaseArtifactGenerator
from services.artifacts.models import GeneratedArtifactRecord, PdfReportData

logger = logging.getLogger(__name__)


class PdfReportGenerator(BaseArtifactGenerator):
    """Generates real, styled PDF engineering reports using reportlab."""

    @property
    def artifact_type(self) -> str:
        return "pdf"

    async def generate(
        self,
        data: PdfReportData,
        output_dir: Path,
        task_id: Optional[str] = None,
    ) -> GeneratedArtifactRecord:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_clean = data.equipment_tag.replace("-", "_").replace(" ", "_")
        filename = f"MRPL_Report_{tag_clean}_{timestamp}.pdf"
        file_path = output_dir / filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=12,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0EA5E9"),
            spaceAfter=18,
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=10,
        )

        elements = [
            Paragraph(f"<b>{data.title}</b>", title_style),
            Paragraph(
                f"EQUIPMENT: {data.equipment_tag} | GENERATED ON-PREMISE: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}",
                subtitle_style,
            ),
            Spacer(1, 10),
        ]

        for p_text in data.paragraphs:
            elements.append(Paragraph(p_text, body_style))

        if data.table_headers and data.table_rows:
            elements.append(Spacer(1, 15))
            table_data = [data.table_headers] + data.table_rows
            t = Table(table_data, colWidths=[120, 150, 100, 100])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ]
                )
            )
            elements.append(t)

        doc.build(elements)

        file_bytes = file_path.read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        artifact_id = generate_uuid("ART")

        return GeneratedArtifactRecord(
            artifact_id=artifact_id,
            task_id=task_id or data.task_id,
            filename=filename,
            type="pdf",
            created_at=datetime.now().isoformat(),
            source_documents=data.source_documents,
            models_used=data.models_used,
            verification_status="verified",
            sha256_hash=sha256,
            size_bytes=len(file_bytes),
            file_path=str(file_path),
            download_url=f"/api/v1/artifacts/{artifact_id}/download",
            metadata={"title": data.title, "equipment_tag": data.equipment_tag},
        )
