from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.agent.tools.registry import ToolRegistry
from services.sovereignty.service import SovereigntyService

router = APIRouter()


class ToolInvokeRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = None


def get_tool_registry() -> ToolRegistry:
    return ToolRegistry()


@router.get("", response_model=List[Dict[str, Any]])
def list_available_tools(registry: ToolRegistry = Depends(get_tool_registry)) -> List[Dict[str, Any]]:
    """List all registered sovereign tools with schemas, descriptions, and required permissions."""
    return registry.list_tools()


@router.get("/{tool_name}")
def get_tool_details(tool_name: str, registry: ToolRegistry = Depends(get_tool_registry)) -> Dict[str, Any]:
    """Retrieve metadata and input/output schema for a specific tool."""
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema,
        "permissions": [p.value for p in tool.permissions],
    }


@router.post("/invoke")
async def invoke_tool_endpoint(
    req: ToolInvokeRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> Dict[str, Any]:
    """Execute a sovereign tool securely through the ToolRegistry."""
    result, record = await registry.invoke_tool(
        tool_name=req.tool_name,
        arguments=req.arguments,
        context=req.context,
    )
    return {
        "success": result.success,
        "tool_name": result.tool_name,
        "output": result.output,
        "error": result.error,
        "record": record.dict(),
    }
