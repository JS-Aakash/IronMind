from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union
from services.document_intelligence.models import OcrTextLine


class BaseOcrEngine(ABC):
    """Abstract sovereign on-premise OCR engine."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        pass

    @abstractmethod
    def extract_text_and_boxes(self, image_input: Union[bytes, Path, str]) -> List[OcrTextLine]:
        """Extract text lines with optional bounding boxes from an image or scanned page."""
        pass
