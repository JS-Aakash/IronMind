from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from apps.backend.app.core.dependencies import get_audit_service, get_sovereignty_service
from packages.shared.models.schemas import AuditLogEntry
from services.audit.models import AuditEvent, TaskAuditSummary
from services.audit.service import AuditService
from services.sovereignty import SovereigntyService

router = APIRouter(prefix="/audit", tags=["Audit & Provenance Trail"])


@router.get("", response_model=List[TaskAuditSummary])
async def list_task_audit_summaries(
    limit: int = Query(50, ge=1, le=200),
    audit_svc: AuditService = Depends(get_audit_service),
):
    """Retrieve chronologically ordered task execution audit summaries for frontend timeline rendering."""
    return audit_svc.list_audit_trails(limit=limit)


@router.get("/logs", response_model=List[AuditLogEntry])
async def list_security_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Retrieve chronologically ordered general sovereignty security & compliance audit logs."""
    return sovereignty_svc.list_audit_logs(limit=limit)


@router.get("/{task_id}", response_model=TaskAuditSummary)
async def get_task_audit_trail(
    task_id: str,
    audit_svc: AuditService = Depends(get_audit_service),
):
    """Retrieve full chronological provenance, tool invocations, model calls, and artifact hashes for a task."""
    trail = audit_svc.get_task_audit(task_id)
    if not trail:
        raise HTTPException(status_code=404, detail=f"Audit trail for task '{task_id}' not found.")
    return trail


@router.get("/{task_id}/events", response_model=List[AuditEvent])
async def list_task_events(
    task_id: str,
    audit_svc: AuditService = Depends(get_audit_service),
):
    """Retrieve raw chronological execution events for a specific task."""
    trail = audit_svc.get_task_audit(task_id)
    if not trail:
        raise HTTPException(status_code=404, detail=f"Audit events for task '{task_id}' not found.")
    return trail.events
