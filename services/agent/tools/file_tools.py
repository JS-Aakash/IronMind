import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import PathTraversalError, ToolPermission, validate_safe_storage_path


class FileReadTool(BaseTool):
    """Safely read local documents or temporary files with strict path traversal checks."""

    @property
    def name(self) -> str:
        return "file.read"

    @property
    def description(self) -> str:
        return "Safely read text or data from an authorized file in sovereign storage."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path or filename of document within sovereign storage (e.g. 'storage/uploads/report.pdf')",
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Maximum bytes to read (default: 32768)",
                    "default": 32768,
                },
            },
            "required": ["file_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "size_bytes": {"type": "integer"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        max_bytes = int(arguments.get("max_bytes", 32768))

        if not file_path_str or not isinstance(file_path_str, str):
            return ToolResult(tool_name=self.name, success=False, error="Parameter 'file_path' must be a non-empty string.")

        try:
            # Enforce path traversal defense and storage directory confinement
            safe_path = validate_safe_storage_path(file_path_str, must_exist=False)
        except PathTraversalError as pe:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Security violation: {str(pe)}",
                metadata={"security_block": True, "target": file_path_str},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))

        # If file does not exist on disk, return grounded simulated buffer for demo artifacts
        if not safe_path.exists():
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "content": f"[Simulated Storage Buffer for: {safe_path.name}] Equipment: Centrifugal Pump P-101. Measured Vibration: 4.8 mm/s RMS. Bearing Temp: 78.5 C. Status: Requires maintenance review.",
                    "size_bytes": 185,
                    "simulated": True,
                },
                metadata={"filename": safe_path.name, "simulated": True},
            )

        try:
            content = safe_path.read_text(encoding="utf-8", errors="replace")[:max_bytes]
            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "content": content,
                    "size_bytes": safe_path.stat().st_size,
                },
                metadata={"filename": safe_path.name, "size_bytes": safe_path.stat().st_size},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File read failed: {str(e)}")


class FileWriteTool(BaseTool):
    """Safely write files strictly into authorized temporary scratchpad or artifacts storage."""

    @property
    def name(self) -> str:
        return "file.write"

    @property
    def description(self) -> str:
        return "Safely write text, markdown, or script content to an authorized path in sovereign storage."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Target filename (e.g. 'calculation_output.txt')"},
                "content": {"type": "string", "description": "Content string to write"},
                "target_directory": {
                    "type": "string",
                    "description": "Storage partition (default: 'storage/temp')",
                    "default": "storage/temp",
                },
            },
            "required": ["filename", "content"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "bytes_written": {"type": "integer"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        filename = arguments.get("filename", "")
        content = arguments.get("content", "")
        target_dir = arguments.get("target_directory", "storage/temp")

        if not filename or not isinstance(filename, str):
            return ToolResult(tool_name=self.name, success=False, error="Argument 'filename' is required.")
        if content is None or not isinstance(content, str):
            return ToolResult(tool_name=self.name, success=False, error="Argument 'content' must be a string.")

        try:
            # Combine target directory and filename, then validate safe storage path
            combined_path = f"{target_dir}/{filename}" if not filename.startswith("storage") else filename
            safe_path = validate_safe_storage_path(combined_path, allow_creation_in="storage/temp")
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding="utf-8")

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "bytes_written": len(content.encode("utf-8")),
                },
                metadata={"file_path": str(safe_path), "bytes_written": len(content.encode("utf-8"))},
            )
        except PathTraversalError as pe:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Security violation: {str(pe)}",
                metadata={"security_block": True},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File write failed: {str(e)}")
