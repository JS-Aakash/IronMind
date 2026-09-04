import logging
import time
from typing import Any, Dict, List, Optional

from packages.shared.utils.helpers import generate_uuid
from services.agent.state import ToolCallRecord
from services.agent.tools.artifact_tools import GenerateDocxApprovalNoteTool
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.calculation_tools import StepByStepCalculationTool
from services.agent.tools.code_tools import PythonExecuteTool, PythonSandboxTool
from services.agent.tools.doc_tools import (
    DocumentCreateTool,
    DocumentModifyDocxTool,
    DocumentOcrParseTool,
    DocumentReadDocxTool,
)
from services.agent.tools.extended_tools import (
    PdfCreateTool,
    PresentationCreateTool,
    SpreadsheetCreateTool,
)
from services.agent.tools.file_tools import (
    FileCopyTool,
    FileReadTool,
    FileRenameTool,
    FileWriteTool,
)
from services.agent.tools.math_tools import CalculatorTool
from services.agent.tools.presentation_tools import PresentationModifyPptxTool
from services.agent.tools.rag_tools import KnowledgeSearchTool
from services.agent.tools.security import PathTraversalError, SecurityViolationError, ToolPermission
from services.agent.tools.spreadsheet_tools import (
    SpreadsheetInspectTool,
    SpreadsheetModifyTool,
)
from services.agent.tools.vision_tools import VisionAnalyzeTool
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry providing controlled, validated, permissioned tool execution for the Agent Orchestrator."""

    FORBIDDEN_SHELL_PATTERNS = [
        "os.system",
        "subprocess.Popen",
        "subprocess.run",
        "subprocess.call",
        "powershell",
        "cmd.exe",
        "/bin/sh",
        "/bin/bash",
        "rm -rf",
        "del /f",
        "format c:",
        "curl http",
        "wget http",
        "nc -e",
    ]

    def __init__(self, sovereignty_service: Optional[SovereigntyService] = None):
        self.sovereignty_service = sovereignty_service or SovereigntyService()
        self._tools: Dict[str, BaseTool] = {}
        self._initialize_default_tools()

    def _initialize_default_tools(self) -> None:
        """Register the core and extended sovereign industrial tools."""
        tools: List[BaseTool] = [
            # File Operations
            FileReadTool(),
            FileWriteTool(),
            FileCopyTool(),
            FileRenameTool(),
            # Calculations
            CalculatorTool(),
            StepByStepCalculationTool(),
            # Knowledge Retrieval
            KnowledgeSearchTool(),
            # Code Execution & Sandbox
            PythonExecuteTool(),
            PythonSandboxTool(),  # Alias
            # Document Tools
            DocumentCreateTool(),
            GenerateDocxApprovalNoteTool(),  # Alias
            DocumentOcrParseTool(),
            DocumentReadDocxTool(),
            DocumentModifyDocxTool(),
            # Spreadsheet Tools
            SpreadsheetCreateTool(),
            SpreadsheetInspectTool(),
            SpreadsheetModifyTool(),
            # Presentation Tools
            PresentationCreateTool(),
            PresentationModifyPptxTool(),
            # Report Tools
            PdfCreateTool(),
            # Vision Tools
            VisionAnalyzeTool(),
        ]
        for t in tools:
            self._tools[t.name] = t

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        self._tools[tool.name] = tool
        logger.info("Registered sovereign tool: %s", tool.name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by identifier."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """Retrieve all registered BaseTool instances."""
        return list(self._tools.values())

    def list_tools(self) -> List[Dict[str, Any]]:
        """List metadata, schemas, and required permissions for all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
                "permissions": [p.value for p in t.permissions],
            }
            for t in self._tools.values()
        ]

    def _validate_arguments_against_schema(self, tool: BaseTool, arguments: Dict[str, Any]) -> Optional[str]:
        """Validate that all required parameters are supplied and no forbidden patterns exist."""
        if not isinstance(arguments, dict):
            return "Tool arguments must be passed as a dictionary/object."

        schema = tool.input_schema
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments or arguments[field] is None:
                return f"Missing required parameter: '{field}'."

        # Check for forbidden arbitrary shell execution attempts in string arguments
        for k, v in arguments.items():
            if isinstance(v, str):
                for forbidden in self.FORBIDDEN_SHELL_PATTERNS:
                    if forbidden in v.lower():
                        return f"Security Policy Violation: Forbidden shell/command execution pattern detected ('{forbidden}')."

        return None

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[ToolResult, ToolCallRecord]:
        """Invoke a tool with schema validation, permission checks, audit logging, and error capture."""
        start_time = time.perf_counter()
        call_id = generate_uuid("CALL")

        tool = self.get_tool(tool_name)
        if not tool:
            err_msg = f"Tool '{tool_name}' is not registered in the sovereign tool registry."
            result = ToolResult(tool_name=tool_name, success=False, error=err_msg)
            record = ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                error=err_msg,
                success=False,
                latency_ms=0.0,
            )
            self.sovereignty_service.log_event(
                event_type="TOOL_NOT_FOUND",
                source_service="Tool Registry",
                details={"tool": tool_name, "call_id": call_id},
            )
            return result, record

        # 1. Argument & Schema Validation
        validation_error = self._validate_arguments_against_schema(tool, arguments)
        if validation_error:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            result = ToolResult(tool_name=tool_name, success=False, error=validation_error)
            record = ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                error=validation_error,
                success=False,
                latency_ms=latency_ms,
            )
            self.sovereignty_service.log_event(
                event_type="TOOL_VALIDATION_ERROR",
                source_service="Tool Registry",
                details={"tool": tool_name, "error": validation_error, "call_id": call_id},
            )
            return result, record

        # 2. Execution
        try:
            logger.info("Executing sovereign tool [%s] (call_id=%s)", tool_name, call_id)
            result = await tool.execute(arguments=arguments, context=context)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            record = ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                output=result.output,
                error=result.error,
                success=result.success,
                latency_ms=latency_ms,
            )

            # Audit logging
            self.sovereignty_service.log_event(
                event_type="TOOL_EXECUTED",
                source_service="Tool Registry",
                details={
                    "tool": tool_name,
                    "call_id": call_id,
                    "success": result.success,
                    "latency_ms": latency_ms,
                    "error": result.error,
                },
            )
            return result, record

        except SecurityViolationError as se:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning("Security violation in tool %s: %s", tool_name, str(se))
            result = ToolResult(tool_name=tool_name, success=False, error=f"Security violation: {str(se)}")
            record = ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                error=str(se),
                success=False,
                latency_ms=latency_ms,
            )
            self.sovereignty_service.log_event(
                event_type="TOOL_SECURITY_VIOLATION",
                source_service="Tool Registry",
                details={"tool": tool_name, "violation": str(se), "call_id": call_id},
            )
            return result, record

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception("Unexpected failure executing tool %s: %s", tool_name, str(e))
            result = ToolResult(tool_name=tool_name, success=False, error=f"Internal tool error: {str(e)}")
            record = ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                arguments=arguments,
                error=str(e),
                success=False,
                latency_ms=latency_ms,
            )
            return result, record
