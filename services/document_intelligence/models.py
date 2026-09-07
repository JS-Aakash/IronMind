from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class OcrTextLine(BaseModel):
    text: str
    confidence: float = 1.0
    bbox: Optional[BoundingBox] = None


class TableData(BaseModel):
    table_id: str
    page_number: int = 1
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    caption: Optional[str] = None


class ImageRegion(BaseModel):
    image_id: str
    page_number: int = 1
    image_type: str = "diagram"  # "pid" | "diagram" | "photo" | "chart"
    bbox: Optional[BoundingBox] = None
    description: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class VisualAnalysis(BaseModel):
    equipment_tags: List[str] = Field(default_factory=list)
    observed_anomalies: List[str] = Field(default_factory=list)
    measured_parameters: Dict[str, Any] = Field(default_factory=dict)
    diagram_type: Optional[str] = None
    summary: str = ""


class PageData(BaseModel):
    page_number: int
    raw_text: str = ""
    ocr_applied: bool = False
    tables: List[TableData] = Field(default_factory=list)
    images: List[ImageRegion] = Field(default_factory=list)
    visual_analysis: Optional[VisualAnalysis] = None


class NormalizedDocument(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    sha256_hash: str
    total_pages: int
    pages: List[PageData] = Field(default_factory=list)
    full_text: str = ""
    extracted_tables: List[TableData] = Field(default_factory=list)
    extracted_equipment_tags: List[str] = Field(default_factory=list)
    summary: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)
