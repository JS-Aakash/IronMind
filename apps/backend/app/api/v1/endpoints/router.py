from fastapi import APIRouter, Depends
from apps.backend.app.core.dependencies import get_model_router, get_sovereignty_service
from services.model_gateway.router import ModelRouter
from services.model_gateway.router_models import (
    CapabilityAnalysis,
    RoutingDecision,
    RoutingRequest,
)
from services.sovereignty import SovereigntyService

router = APIRouter(prefix="/router", tags=["Model Router"])


@router.post("/analyze", response_model=CapabilityAnalysis)
async def analyze_task_capabilities(
    request: RoutingRequest,
    model_router: ModelRouter = Depends(get_model_router),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Analyze a user prompt and attached documents to extract required AI capabilities."""
    analysis = model_router.analyze_capabilities(request)
    sovereignty_svc.log_event(
        event_type="TASK_CAPABILITY_ANALYSIS",
        source_service="Model Router",
        details={
            "task_type": analysis.task_type.value,
            "detected_capabilities": analysis.detected_capabilities,
            "requires_vision": analysis.requires_vision,
            "requires_coding": analysis.requires_coding,
        },
    )
    return analysis


@router.post("/select", response_model=RoutingDecision)
async def select_model_for_task(
    request: RoutingRequest,
    model_router: ModelRouter = Depends(get_model_router),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Perform deterministic scoring and auto-select the best local open-weight model(s)."""
    decision = model_router.route_task(request)
    sovereignty_svc.log_event(
        event_type="MODEL_AUTO_ROUTED",
        source_service="Model Router",
        details={
            "task_type": decision.task_type.value,
            "primary_model": decision.primary_model,
            "stage_models": decision.stage_models,
            "reason": decision.routing_reason,
        },
    )
    return decision
