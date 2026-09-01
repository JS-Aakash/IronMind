import logging
from pathlib import Path
from typing import List, Optional, Union

from services.document_intelligence.models import BoundingBox, OcrTextLine
from services.document_intelligence.ocr.base import BaseOcrEngine

logger = logging.getLogger(__name__)


class PaddleOcrEngine(BaseOcrEngine):
    """Local PaddleOCR engine integration for multilingual on-premise industrial text recognition."""

    def __init__(self, use_angle_cls: bool = True, lang: str = "en"):
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self._ocr = None
        self._initialized = False

    @property
    def engine_name(self) -> str:
        return "PaddleOCR"

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang, show_log=False)
            self._initialized = True
            logger.info("PaddleOCR engine loaded successfully on local hardware.")
            return True
        except ImportError:
            logger.warning("PaddleOCR library is not installed in the current Python environment.")
            return False
        except Exception as e:
            logger.warning("PaddleOCR failed to initialize: %s", str(e))
            return False

    def extract_text_and_boxes(self, image_input: Union[bytes, Path, str]) -> List[OcrTextLine]:
        if not self._ensure_initialized() or not self._ocr:
            raise RuntimeError("PaddleOCR is not available.")

        img_path = str(image_input) if isinstance(image_input, (Path, str)) else None
        if not img_path:
            # Save bytes to temp file if passed as bytes
            import tempfile
            with tempfile.NamedTemporaryFile("wb", suffix=".png", delete=False) as f:
                f.write(image_input)
                img_path = f.name

        try:
            result = self._ocr.ocr(img_path, cls=self.use_angle_cls)
            lines: List[OcrTextLine] = []
            if result and result[0]:
                for line in result[0]:
                    box_points = line[0]  # [[x0,y0], [x1,y0], [x1,y1], [x0,y1]]
                    text_info = line[1]   # ("Text", confidence)
                    x_coords = [p[0] for p in box_points]
                    y_coords = [p[1] for p in box_points]
                    bbox = BoundingBox(
                        x0=float(min(x_coords)),
                        y0=float(min(y_coords)),
                        x1=float(max(x_coords)),
                        y1=float(max(y_coords)),
                    )
                    lines.append(OcrTextLine(text=text_info[0], confidence=float(text_info[1]), bbox=bbox))
            return lines
        except Exception as e:
            logger.error("PaddleOCR recognition error: %s", str(e))
            return []
