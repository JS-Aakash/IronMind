from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int = 1
    section: Optional[str] = None
    text: str
    embedding: Optional[List[float]] = None
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_name: str
    page_number: int
    section: Optional[str] = None
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    document_name: str
    page: int
    section: Optional[str] = None
    snippet: str


class RetrievalResult(BaseModel):
    query: str
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    assembled_context: str = ""
    top_k: int = 3
    total_indexed_chunks: int = 0
