import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ExtractedPdfPage:
    def __init__(self, page_number: int, text: str, is_scanned: bool = False, image_bytes: Optional[bytes] = None):
        self.page_number = page_number
        self.text = text
        self.is_scanned = is_scanned
        self.image_bytes = image_bytes


class PdfLayoutExtractor:
    """Extracts text, metadata, and pages from local PDF documents."""

    def extract_pages(self, pdf_input: Union[bytes, Path, str]) -> List[ExtractedPdfPage]:
        """Extract pages and determine if pages require OCR."""
        pages: List[ExtractedPdfPage] = []

        raw_bytes: Optional[bytes] = None
        if isinstance(pdf_input, (Path, str)):
            pdf_path = Path(pdf_input)
            if pdf_path.exists():
                raw_bytes = pdf_path.read_bytes()
            else:
                raw_bytes = b""
        else:
            raw_bytes = pdf_input

        # Try pypdf / PyPDF2 / pdfplumber if installed
        extracted = False
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                # If page has very little text (< 50 chars), mark as scanned needing OCR
                is_scanned = len(page_text.strip()) < 50
                pages.append(
                    ExtractedPdfPage(
                        page_number=idx + 1,
                        text=page_text.strip(),
                        is_scanned=is_scanned,
                    )
                )
            extracted = True
        except ImportError:
            logger.debug("pypdf not installed, using binary / text heuristic parser.")
        except Exception as e:
            logger.warning("pypdf parsing encountered an error: %s", str(e))

        if not extracted or not pages:
            is_real_pdf = raw_bytes[:5] == b"%PDF-"
            text_candidate = ""
            if not is_real_pdf:
                try:
                    text_candidate = raw_bytes.decode("utf-8", errors="ignore")
                except Exception:
                    pass

            if text_candidate and len(text_candidate.strip()) > 30:
                pages.append(
                    ExtractedPdfPage(
                        page_number=1,
                        text=text_candidate.strip(),
                        is_scanned=False,
                    )
                )
            else:
                # Mark as scanned page 1 requiring OCR
                pages.append(
                    ExtractedPdfPage(
                        page_number=1,
                        text="",
                        is_scanned=True,
                        image_bytes=raw_bytes,
                    )
                )

        return pages
