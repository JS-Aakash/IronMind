import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from services.document_intelligence.models import NormalizedDocument
from services.document_intelligence.service import DocumentIntelligenceService

router = APIRouter()


class DocumentProcessPathRequest(BaseModel):
    file_path: str = Field(description="Local path to document in sovereign storage (e.g. 'storage/uploads/report.pdf')")
    enable_vision_llm: bool = Field(default=True, description="Enable Qwen2.5-VL visual analysis")


def get_doc_service() -> DocumentIntelligenceService:
    return DocumentIntelligenceService()


@router.get("", response_model=List[Dict[str, Any]])
def list_processed_documents(service: DocumentIntelligenceService = Depends(get_doc_service)) -> List[Dict[str, Any]]:
    """List all processed and normalized sovereign documents."""
    return service.list_documents()


@router.get("/{document_id}", response_model=NormalizedDocument)
def get_processed_document(document_id: str, service: DocumentIntelligenceService = Depends(get_doc_service)) -> NormalizedDocument:
    """Retrieve normalized document structure and extracted tables/tags."""
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Processed document '{document_id}' not found.")
    return doc


@router.post("/upload")
async def upload_task_document(
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Upload a temporary task attachment (PDF, PNG, JPG, JPEG, DOCX) to the local staging workspace."""
    uploads_dir = Path("storage/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "task_attachment"
    target_path = uploads_dir / filename
    
    file_bytes = await file.read()
    target_path.write_bytes(file_bytes)
    
    return {
        "filename": filename,
        "file_path": str(target_path),
        "size_bytes": len(file_bytes),
        "content_type": file.content_type or "application/octet-stream",
        "status": "staged_for_task",
    }


@router.post("/process", response_model=NormalizedDocument)
async def process_document_endpoint(
    req: Optional[DocumentProcessPathRequest] = None,
    file: Optional[UploadFile] = File(None),
    enable_vision_llm: bool = Form(True),
    service: DocumentIntelligenceService = Depends(get_doc_service),
) -> NormalizedDocument:
    """Process a confidential PDF, PNG, JPG, or JPEG document through the Sovereign Document Intelligence Pipeline."""
    if file:
        file_bytes = await file.read()
        return await service.process_document(
            file_input=file_bytes,
            filename=file.filename or "uploaded_file.pdf",
            enable_vision_llm=enable_vision_llm,
        )
    elif req and req.file_path:
        return await service.process_document(
            file_input=req.file_path,
            filename=Path(req.file_path).name,
            enable_vision_llm=req.enable_vision_llm,
        )
    else:
        raise HTTPException(status_code=400, detail="Either a file upload or a JSON 'file_path' must be provided.")
