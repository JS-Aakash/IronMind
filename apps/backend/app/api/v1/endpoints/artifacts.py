from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from apps.backend.app.core.dependencies import get_artifacts_service
from services.artifacts.generators.code_generator import SourceCodeArtifactData
from services.artifacts.models import (
    ApprovalNoteData,
    GeneratedArtifactRecord,
    PdfReportData,
    PresentationData,
    SpreadsheetData,
)
from services.artifacts.service import ArtifactsService

router = APIRouter(prefix="/artifacts", tags=["Artifacts & Deliverables"])


@router.get("", response_model=List[GeneratedArtifactRecord])
async def list_artifacts(artifacts_svc: ArtifactsService = Depends(get_artifacts_service)):
    """List all generated deliverables and verification hashes."""
    return artifacts_svc.list_artifacts()


@router.get("/{artifact_id}", response_model=GeneratedArtifactRecord)
async def get_artifact(artifact_id: str, artifacts_svc: ArtifactsService = Depends(get_artifacts_service)):
    """Retrieve details and cryptographic provenance of a specific artifact."""
    artifact = artifacts_svc.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found.")
    return artifact


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str, artifacts_svc: ArtifactsService = Depends(get_artifacts_service)):
    """Permanently delete a business deliverable and remove from registry."""
    success = artifacts_svc.delete_artifact(artifact_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found.")
    return {"status": "deleted", "artifact_id": artifact_id}


@router.get("/{artifact_id}/download")
async def download_artifact_file(artifact_id: str, artifacts_svc: ArtifactsService = Depends(get_artifacts_service)):
    """Download the real, generated binary/text artifact file."""
    file_path = artifacts_svc.get_artifact_file_path(artifact_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact file for {artifact_id} not found on disk.")
    
    # Determine media type
    ext = file_path.suffix.lower()
    media_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pdf": "application/pdf",
        ".py": "text/x-python",
        ".txt": "text/plain",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=media_type,
    )


@router.post("/approval-note", response_model=GeneratedArtifactRecord)
async def generate_approval_note(
    data: Optional[ApprovalNoteData] = None,
    task_id: Optional[str] = Query(None),
    artifacts_svc: ArtifactsService = Depends(get_artifacts_service),
):
    """Generate a real styled DOCX Approval Note with MRPL branding and signature blocks."""
    return await artifacts_svc.generate_approval_note(data=data, task_id=task_id)


@router.post("/spreadsheet", response_model=GeneratedArtifactRecord)
async def generate_spreadsheet(
    data: Optional[SpreadsheetData] = None,
    task_id: Optional[str] = Query(None),
    artifacts_svc: ArtifactsService = Depends(get_artifacts_service),
):
    """Generate a real styled XLSX spreadsheet."""
    return await artifacts_svc.generate_spreadsheet(data=data, task_id=task_id)


@router.post("/presentation", response_model=GeneratedArtifactRecord)
async def generate_presentation(
    data: Optional[PresentationData] = None,
    task_id: Optional[str] = Query(None),
    artifacts_svc: ArtifactsService = Depends(get_artifacts_service),
):
    """Generate a real styled PPTX presentation deck."""
    return await artifacts_svc.generate_presentation(data=data, task_id=task_id)


@router.post("/pdf", response_model=GeneratedArtifactRecord)
async def generate_pdf(
    data: Optional[PdfReportData] = None,
    task_id: Optional[str] = Query(None),
    artifacts_svc: ArtifactsService = Depends(get_artifacts_service),
):
    """Generate a real styled PDF document."""
    return await artifacts_svc.generate_pdf(data=data, task_id=task_id)


@router.post("/code", response_model=GeneratedArtifactRecord)
async def generate_code_artifact(
    data: SourceCodeArtifactData,
    task_id: Optional[str] = Query(None),
    artifacts_svc: ArtifactsService = Depends(get_artifacts_service),
):
    """Generate a verified source code deliverable."""
    return await artifacts_svc.generate_code_artifact(data=data, task_id=task_id)
