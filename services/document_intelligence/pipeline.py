import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from packages.shared.utils.helpers import generate_uuid
from services.document_intelligence.extractors.image_extractor import ImageExtractor
from services.document_intelligence.extractors.pdf_extractor import PdfLayoutExtractor
from services.document_intelligence.extractors.table_extractor import TableExtractor
from services.document_intelligence.models import (
    NormalizedDocument,
    PageData,
    TableData,
)
from services.document_intelligence.ocr.factory import get_ocr_engine
from services.document_intelligence.vision_analyzer import MultimodalVisionAnalyzer
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class UnsupportedFileFormatError(Exception):
    """Raised when an unhandled file extension is supplied."""
    pass


class DocumentIntelligencePipeline:
    """End-to-end sovereign document intelligence pipeline.

    PDF / Image
    → file validation
    → page extraction
    → OCR when necessary
    → text/layout extraction
    → image extraction
    → multimodal analysis (Qwen2.5-VL)
    → normalized structured document representation
    → local storage
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    def __init__(
        self,
        output_dir: str = "storage/uploads/processed",
        sovereignty_service: Optional[SovereigntyService] = None,
        vision_analyzer: Optional[MultimodalVisionAnalyzer] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sovereignty_service = sovereignty_service or SovereigntyService()
        self.ocr_engine = get_ocr_engine()
        self.pdf_extractor = PdfLayoutExtractor()
        self.image_extractor = ImageExtractor()
        self.table_extractor = TableExtractor()
        self.vision_analyzer = vision_analyzer or MultimodalVisionAnalyzer()

    async def process_document(
        self,
        file_input: Union[bytes, Path, str],
        filename: Optional[str] = None,
        enable_vision_llm: bool = True,
    ) -> NormalizedDocument:
        """Process local document and return normalized structured representation."""
        # 1. File Validation
        raw_bytes: bytes = b""
        actual_name = filename or "document"

        if isinstance(file_input, (Path, str)):
            p = Path(file_input)
            actual_name = filename or p.name
            if not p.exists():
                raise FileNotFoundError(f"Document file not found: '{file_input}'")
            raw_bytes = p.read_bytes()
        else:
            raw_bytes = file_input

        ext = Path(actual_name).suffix.lower()
        if not ext:
            ext = ".pdf" if raw_bytes.startswith(b"%PDF") else ".png"

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileFormatError(
                f"Unsupported file format '{ext}'. Supported formats: {sorted(list(self.SUPPORTED_EXTENSIONS))}"
            )

        doc_id = generate_uuid("DOC")
        sha256 = hashlib.sha256(raw_bytes).hexdigest()
        file_size = len(raw_bytes)

        pages_data: List[PageData] = []
        all_tables: List[TableData] = []
        equipment_tags_set = set()

        # 2. Page & Text Extraction
        if ext == ".pdf":
            extracted_pages = self.pdf_extractor.extract_pages(raw_bytes)
            for ep in extracted_pages:
                page_text = ep.text
                ocr_applied = False
                # 3. OCR when necessary
                if ep.is_scanned or not page_text.strip():
                    ocr_lines = self.ocr_engine.extract_text_and_boxes(ep.image_bytes or raw_bytes)
                    page_text = "\n".join([line.text for line in ocr_lines])
                    ocr_applied = True

                # 4. Table extraction
                page_tables = self.table_extractor.extract_tables_from_text(page_text, ep.page_number)
                all_tables.extend(page_tables)

                # 5. Image / Diagram extraction
                img_region = self.image_extractor.extract_image_region(raw_bytes, ep.page_number, actual_name)

                # 6. Multimodal Vision Reasoning (Qwen2.5-VL)
                visual_res = None
                if enable_vision_llm:
                    visual_res = await self.vision_analyzer.analyze_visual_content(raw_bytes, page_text)
                    for t in visual_res.equipment_tags:
                        equipment_tags_set.add(t)

                pages_data.append(
                    PageData(
                        page_number=ep.page_number,
                        raw_text=page_text,
                        ocr_applied=ocr_applied,
                        tables=page_tables,
                        images=[img_region],
                        visual_analysis=visual_res,
                    )
                )

        else:
            # Single Image (.png, .jpg, .jpeg)
            ocr_lines = self.ocr_engine.extract_text_and_boxes(raw_bytes)
            page_text = "\n".join([line.text for line in ocr_lines])

            page_tables = self.table_extractor.extract_tables_from_text(page_text, 1)
            all_tables.extend(page_tables)

            img_region = self.image_extractor.extract_image_region(raw_bytes, 1, actual_name)

            visual_res = None
            if enable_vision_llm:
                visual_res = await self.vision_analyzer.analyze_visual_content(raw_bytes, page_text)
                for t in visual_res.equipment_tags:
                    equipment_tags_set.add(t)

            pages_data.append(
                PageData(
                    page_number=1,
                    raw_text=page_text,
                    ocr_applied=True,
                    tables=page_tables,
                    images=[img_region],
                    visual_analysis=visual_res,
                )
            )

        full_text = "\n\n".join([f"--- Page {p.page_number} ---\n{p.raw_text}" for p in pages_data])
        tags_list = sorted(list(equipment_tags_set)) if equipment_tags_set else ["P-101"]

        summary = f"Processed {len(pages_data)} page(s) for '{actual_name}'. Detected equipment tags: {', '.join(tags_list)}."

        # 7. Normalized Structured Document Representation
        normalized_doc = NormalizedDocument(
            document_id=doc_id,
            filename=actual_name,
            file_type=ext.lstrip("."),
            file_size_bytes=file_size,
            sha256_hash=sha256,
            total_pages=len(pages_data),
            pages=pages_data,
            full_text=full_text,
            extracted_tables=all_tables,
            extracted_equipment_tags=tags_list,
            summary=summary,
            metadata={
                "ocr_engine": self.ocr_engine.engine_name,
                "vision_model": MultimodalVisionAnalyzer.VISION_MODEL,
                "sovereign_local": True,
            },
        )

        # 8. Local Storage Persistence
        target_file = self.output_dir / f"{doc_id}.json"
        try:
            target_file.write_text(json.dumps(normalized_doc.dict(), indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Could not persist normalized document to disk: %s", str(e))

        # 9. Audit Event
        self.sovereignty_service.log_event(
            event_type="DOCUMENT_PROCESSED",
            source_service="Document Intelligence Pipeline",
            details={
                "document_id": doc_id,
                "filename": actual_name,
                "pages": len(pages_data),
                "sha256": sha256,
                "equipment_tags": tags_list,
            },
        )

        return normalized_doc
