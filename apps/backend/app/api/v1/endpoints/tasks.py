import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from apps.backend.app.core.dependencies import get_agent_service, get_sovereignty_service
from packages.shared.models.enums import TaskType
from services.agent.service import AgentService
from services.agent.state import AgentState, ExecutionEvent
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Agent Tasks"])


class CreateTaskRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="Task goal, instruction, or engineering description")
    task_type: Optional[TaskType] = Field(default=None, description="Optional manual task classification")
    uploaded_files: List[str] = Field(default_factory=list, description="Associated filenames / uploads")


class ExecuteTaskRequest(BaseModel):
    uploaded_files: List[str] = Field(default_factory=list)


@router.post("", response_model=AgentState)
async def create_task_endpoint(
    request: CreateTaskRequest,
    agent_svc: AgentService = Depends(get_agent_service),
):
    """Create a new industrial AI agent task."""
    state = agent_svc.create_task(
        goal=request.goal,
        task_type=request.task_type,
        uploaded_files=request.uploaded_files,
    )
    return state


@router.get("", response_model=List[AgentState])
async def list_tasks_endpoint(
    limit: int = Query(default=50, ge=1, le=100),
    agent_svc: AgentService = Depends(get_agent_service),
):
    """List recent agent tasks."""
    return agent_svc.list_tasks(limit=limit)


@router.get("/{task_id}", response_model=AgentState)
async def get_task_endpoint(
    task_id: str,
    agent_svc: AgentService = Depends(get_agent_service),
):
    """Get the full state, plan, tool calls, and verification status for a task."""
    state = agent_svc.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return state


@router.post("/{task_id}/execute", response_model=AgentState)
async def execute_task_endpoint(
    task_id: str,
    request: Optional[ExecuteTaskRequest] = None,
    agent_svc: AgentService = Depends(get_agent_service),
):
    """Execute the full ReAct state machine lifecycle (PLAN -> EXECUTE -> OBSERVE -> VERIFY -> COMPLETE)."""
    state = agent_svc.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    files = request.uploaded_files if request else None
    updated_state = await agent_svc.execute_task(task_id, uploaded_files=files)
    return updated_state


@router.get("/{task_id}/events")
async def stream_task_events_endpoint(
    task_id: str,
    agent_svc: AgentService = Depends(get_agent_service),
):
    """Stream real-time agent execution events via Server-Sent Events (SSE)."""
    state = agent_svc.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    async def event_generator():
        try:
            async for event in agent_svc.stream_task_events(task_id):
                payload = json.dumps(event.dict(), default=str)
                yield f"data: {payload}\n\n"
        except Exception as e:
            logger.exception("Error in SSE event stream: %s", str(e))
            yield f"data: {json.dumps({'error': str(e), 'event_type': 'STREAM_ERROR'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
