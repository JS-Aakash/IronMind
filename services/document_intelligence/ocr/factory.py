import logging
from services.document_intelligence.ocr.base import BaseOcrEngine
from services.document_intelligence.ocr.fallback_ocr import FallbackOcrEngine
from services.document_intelligence.ocr.paddle_ocr import PaddleOcrEngine

logger = logging.getLogger(__name__)


def get_ocr_engine(prefer_paddle: bool = True) -> BaseOcrEngine:
    """Factory function returning the best available local OCR engine."""
    if prefer_paddle:
        try:
            engine = PaddleOcrEngine()
            if engine._ensure_initialized():
                return engine
        except Exception:
            logger.info("PaddleOCR not available; switching to sovereign local fallback OCR engine.")

    return FallbackOcrEngine()
