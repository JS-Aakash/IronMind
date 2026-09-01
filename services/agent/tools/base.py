from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.agent.tools.security import ToolPermission


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all secure sovereign local tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier (e.g. 'file.read', 'calculator', 'python.execute')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Clear description of the tool's purpose and functionality."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema defining required and optional parameters."""
        pass

    @property
    def output_schema(self) -> Dict[str, Any]:
        """JSON Schema defining the expected output structure."""
        return {"type": "object"}

    @property
    def permissions(self) -> List[ToolPermission]:
        """List of security permissions required to execute this tool."""
        return []

    # Backward compatibility alias
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return self.input_schema

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the tool safely and return a structured ToolResult."""
        pass
