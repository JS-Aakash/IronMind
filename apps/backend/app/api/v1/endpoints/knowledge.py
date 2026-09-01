import io
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from apps.backend.app.core.dependencies import get_rag_service
from packages.shared.models.schemas import KnowledgeDocument
from services.rag.models import RetrievalResult
from services.rag.service import RagService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & Local RAG"])


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(description="Semantic search query")
    top_k: int = Field(default=3, ge=1, le=20)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class KnowledgeIndexRequest(BaseModel):
    rebuild_embeddings: bool = Field(default=False)


@router.get("/documents", response_model=List[KnowledgeDocument])
async def list_knowledge_documents(rag_svc: RagService = Depends(get_rag_service)):
    """List all indexed local SOPs and industrial manuals."""
    return rag_svc.list_documents()


@router.get("/documents/{doc_id}", response_model=KnowledgeDocument)
async def get_knowledge_document(doc_id: str, rag_svc: RagService = Depends(get_rag_service)):
    """Retrieve metadata for a specific knowledge document."""
    doc = rag_svc.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found in local index.")
    return doc


@router.delete("/documents/{doc_id}")
async def delete_knowledge_document(doc_id: str, rag_svc: RagService = Depends(get_rag_service)):
    """Delete a persistent document and purge its embedded chunks from the vector store."""
    success = rag_svc.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/upload", response_model=KnowledgeDocument)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("SOP"),
    rag_svc: RagService = Depends(get_rag_service),
):
    """Upload and ingest a local SOP, equipment manual, or standard into the sovereign RAG index."""
    file_bytes = await file.read()
    filename = file.filename or "uploaded_sop.txt"

    doc = await rag_svc.ingest_document(
        file_input=file_bytes,
        filename=filename,
        title=title,
        category=category,
    )
    return doc


@router.post("/index")
async def trigger_indexing(
    req: Optional[KnowledgeIndexRequest] = None,
    rag_svc: RagService = Depends(get_rag_service),
) -> Dict[str, Any]:
    """Index or re-index pending local knowledge documents."""
    total_chunks = await rag_svc.index_all_pending_documents()
    return {
        "status": "indexed",
        "total_indexed_chunks": total_chunks,
        "vector_store": "SovereignVectorStore",
    }


@router.post("/search", response_model=RetrievalResult)
async def search_knowledge(
    req: KnowledgeSearchRequest,
    rag_svc: RagService = Depends(get_rag_service),
) -> RetrievalResult:
    """Execute semantic dense retrieval over local SOPs and return structured evidence chunks & citations."""
    return await rag_svc.search(
        query=req.query,
        top_k=req.top_k,
        threshold=req.threshold,
    )
