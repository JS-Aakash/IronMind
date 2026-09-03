import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from apps.backend.app.core.dependencies import get_model_gateway_service, get_sovereignty_service
from packages.shared.models.enums import ModelRole
from packages.shared.models.schemas import ModelInfo
from services.model_gateway.models import (
    GenerationRequest,
    GenerationResponse,
    ModelHealthResponse,
)
from services.model_gateway.service import ModelService
from services.sovereignty import SovereigntyService

router = APIRouter(prefix="/models", tags=["Model Gateway"])


@router.get("", response_model=List[ModelInfo])
async def list_models(model_svc: ModelService = Depends(get_model_gateway_service)):
    """List all registered on-premise open-weight models."""
    return model_svc.list_models()


@router.get("/route", response_model=ModelInfo)
async def route_model(
    role: ModelRole = Query(..., description="Desired functional capability role"),
    model_svc: ModelService = Depends(get_model_gateway_service),
):
    """Dynamically route to best matching local model for a given capability."""
    model = model_svc.route_task_to_model(role)
    if not model:
        raise HTTPException(status_code=404, detail=f"No local model available for role: {role}")
    return model


@router.get("/{name}/health", response_model=ModelHealthResponse)
async def get_model_health(
    name: str,
    model_svc: ModelService = Depends(get_model_gateway_service),
):
    """Check availability and readiness of a local model."""
    return await model_svc.check_model_health(name)


@router.post("/{name}/generate", response_model=GenerationResponse)
async def generate_with_model(
    name: str,
    request: GenerationRequest,
    model_svc: ModelService = Depends(get_model_gateway_service),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Unified inference endpoint for text, structured JSON, or multimodal image analysis."""
    # Multimodal image analysis
    if request.images and len(request.images) > 0:
        response = await model_svc.analyze_image(
            model=name,
            prompt=request.prompt,
            images=request.images,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    # Structured JSON generation
    elif request.json_format or request.schema_definition:
        response = await model_svc.generate_structured(
            model=name,
            prompt=request.prompt,
            schema_definition=request.schema_definition,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    # Standard text generation
    else:
        response = await model_svc.generate_text(
            model=name,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stop_sequences=request.stop_sequences,
        )

    # Log to sovereignty and audit trail
    sovereignty_svc.log_event(
        event_type="LOCAL_MODEL_INFERENCE",
        source_service="Model Gateway",
        details={
            "model": response.model,
            "provider": response.provider,
            "tokens": response.total_tokens,
            "latency_ms": response.latency_ms,
        },
    )

    return response


@router.post("/{name}/stream")
async def stream_with_model(
    name: str,
    request: GenerationRequest,
    model_svc: ModelService = Depends(get_model_gateway_service),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Server-Sent Events (SSE) streaming endpoint for real-time token emission."""
    sovereignty_svc.log_event(
        event_type="STREAM_INFERENCE_START",
        source_service="Model Gateway",
        details={"model": name},
    )

    async def event_generator():
        try:
            async for chunk in model_svc.stream(
                model=name,
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                yield f"data: {json.dumps(chunk.dict())}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'is_done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/test-qwen3", response_model=GenerationResponse)
async def test_qwen3_endpoint(
    prompt: Optional[str] = Query(default="Explain centrifugal pump cavitation in 2 bullet points.", description="Test prompt"),
    model_svc: ModelService = Depends(get_model_gateway_service),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Test endpoint that sends a sample engineering prompt to qwen3:8b."""
    try:
        response = await model_svc.generate_text(
            model="qwen3:8b",
            prompt=prompt or "Explain centrifugal pump cavitation in 2 bullet points.",
            system_prompt="You are an expert refinery engineering assistant at MRPL.",
            temperature=0.2,
            max_tokens=2048,
        )
    except Exception as e:
        # If Ollama is not running on localhost, fallback gracefully to mock provider to demonstrate endpoint contract
        mock_provider = model_svc.get_provider("mock")
        response = await mock_provider.generate_text(
            model="qwen3:8b",
            prompt=prompt or "Explain centrifugal pump cavitation in 2 bullet points.",
            system_prompt="You are an expert refinery engineering assistant at MRPL.",
        )
        response.text += f"\n[Notice: Ollama was not reachable, served via local mock provider. Error: {str(e)}]"

    sovereignty_svc.log_event(
        event_type="TEST_QWEN3_PROMPT",
        source_service="Model Gateway",
        details={"model": "qwen3:8b", "latency_ms": response.latency_ms},
    )
    return response


@router.get("/status")
async def get_models_status_endpoint(model_svc: ModelService = Depends(get_model_gateway_service)):
    """Get real-time operational status and memory residency for all 4 primary industrial models."""
    return await model_svc.get_models_status()


@router.post("/{model_id}/load", response_model=ModelInfo)
async def load_model(
    model_id: str,
    model_svc: ModelService = Depends(get_model_gateway_service),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Preload model into local VRAM with keep_alive=-1 to eliminate cold-start latency."""
    try:
        model = await model_svc.load_model(model_id)
        sovereignty_svc.log_event(
            event_type="MODEL_LOADED",
            source_service="Model Gateway",
            details={"model_id": model_id, "name": model.name, "status": "LOADED • WARM"},
        )
        return model
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{model_id}/unload", response_model=ModelInfo)
async def unload_model(
    model_id: str,
    model_svc: ModelService = Depends(get_model_gateway_service),
    sovereignty_svc: SovereigntyService = Depends(get_sovereignty_service),
):
    """Explicitly release model from local VRAM to free GPU/system memory."""
    try:
        model = await model_svc.unload_model(model_id)
        sovereignty_svc.log_event(
            event_type="MODEL_UNLOADED",
            source_service="Model Gateway",
            details={"model_id": model_id, "name": model.name, "status": "UNLOADED"},
        )
        return model
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
