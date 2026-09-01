from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends

from apps.backend.app.core.config import settings
from apps.backend.app.core.dependencies import get_sovereignty_service
from services.sovereignty import SovereigntyService

router = APIRouter(tags=["Health & System"])


@router.get("/health", response_model=Dict[str, Any])
async def get_health(sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service)):
    """Health check endpoint for IronMind Sovereign AI Workbench."""
    metrics = sovereignty_svc.get_metrics()
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "sovereignty": {
            "mode": "100% On-Premise Airgap",
            "cloud_egress": "BLOCKED",
            "status": metrics.status,
            "external_calls": metrics.external_calls_count,
        },
        "services": {
            "model_gateway": "ready",
            "agent_orchestrator": "ready",
            "rag_engine": "ready",
            "document_intelligence": "ready",
            "code_sandbox": "ready",
            "artifact_engine": "ready",
            "sovereignty_monitor": "active",
        }
    }
