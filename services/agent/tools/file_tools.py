import hashlib
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import PathTraversalError, ToolPermission, validate_safe_storage_path


class FileReadTool(BaseTool):
    """Safely read local documents or data files with strict path traversal checks and zero mock buffers."""

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
                    "description": "Maximum bytes to read (default: 65536)",
                    "default": 65536,
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
                "sha256_hash": {"type": "string"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        max_bytes = int(arguments.get("max_bytes", 65536))

        if not file_path_str or not isinstance(file_path_str, str):
            return ToolResult(tool_name=self.name, success=False, error="Parameter 'file_path' must be a non-empty string.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=True)
        except PathTraversalError as pe:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"Security violation: {str(pe)}",
                metadata={"security_block": True, "target": file_path_str},
            )
        except FileNotFoundError as fe:
            return ToolResult(tool_name=self.name, success=False, error=str(fe))
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File read error: {str(e)}")

        try:
            raw_bytes = safe_path.read_bytes()
            sha256 = hashlib.sha256(raw_bytes).hexdigest()
            content = raw_bytes[:max_bytes].decode("utf-8", errors="replace")

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "filename": safe_path.name,
                    "content": content,
                    "size_bytes": len(raw_bytes),
                    "sha256_hash": sha256,
                },
                metadata={"filename": safe_path.name, "size_bytes": len(raw_bytes), "sha256": sha256},
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
        return "Safely write text, markdown, CSV, or script content to an authorized path in sovereign storage."

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
                "sha256_hash": {"type": "string"},
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
            combined_path = f"{target_dir}/{filename}" if not filename.startswith("storage") else filename
            safe_path = validate_safe_storage_path(combined_path, allow_creation_in=target_dir)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            raw_bytes = content.encode("utf-8")
            safe_path.write_bytes(raw_bytes)
            sha256 = hashlib.sha256(raw_bytes).hexdigest()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "filename": safe_path.name,
                    "bytes_written": len(raw_bytes),
                    "sha256_hash": sha256,
                },
                metadata={"file_path": str(safe_path), "bytes_written": len(raw_bytes), "sha256": sha256},
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


class FileCopyTool(BaseTool):
    """Safely copy files between authorized sovereign storage partitions."""

    @property
    def name(self) -> str:
        return "file.copy"

    @property
    def description(self) -> str:
        return "Safely copy an existing file from one sovereign storage location to another (e.g. backup before modification)."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_path": {"type": "string", "description": "Path to source file in storage"},
                "destination_path": {"type": "string", "description": "Target destination path or directory in storage"},
            },
            "required": ["source_path", "destination_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_path": {"type": "string"},
                "destination_path": {"type": "string"},
                "bytes_copied": {"type": "integer"},
                "sha256_hash": {"type": "string"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ, ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        source_str = arguments.get("source_path", "")
        dest_str = arguments.get("destination_path", "")

        if not source_str or not dest_str:
            return ToolResult(tool_name=self.name, success=False, error="Both 'source_path' and 'destination_path' are required.")

        try:
            safe_source = validate_safe_storage_path(source_str, must_exist=True)
            
            # Destination path resolution
            if dest_str.endswith("/") or dest_str.endswith("\\") or Path(dest_str).is_dir() or not Path(dest_str).suffix:
                dest_full = f"{dest_str.rstrip('/\\')}/{safe_source.name}"
            else:
                dest_full = dest_str
            safe_dest = validate_safe_storage_path(dest_full, allow_creation_in="storage/artifacts")
            safe_dest.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(str(safe_source), str(safe_dest))

            file_bytes = safe_dest.read_bytes()
            sha256 = hashlib.sha256(file_bytes).hexdigest()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "source_path": str(safe_source),
                    "destination_path": str(safe_dest),
                    "filename": safe_dest.name,
                    "bytes_copied": len(file_bytes),
                    "sha256_hash": sha256,
                },
                metadata={"source": str(safe_source), "destination": str(safe_dest), "sha256": sha256},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File copy failed: {str(e)}")


class FileRenameTool(BaseTool):
    """Safely rename or move a file within authorized sovereign storage partitions."""

    @property
    def name(self) -> str:
        return "file.rename"

    @property
    def description(self) -> str:
        return "Safely rename or move an existing file within authorized sovereign storage directories."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_path": {"type": "string", "description": "Current path to file in storage"},
                "new_name_or_path": {"type": "string", "description": "New filename or full target path in storage"},
            },
            "required": ["source_path", "new_name_or_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "old_path": {"type": "string"},
                "new_path": {"type": "string"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_WRITE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        source_str = arguments.get("source_path") or arguments.get("src_path") or ""
        new_path_str = arguments.get("new_name_or_path") or arguments.get("new_path") or arguments.get("destination_path") or ""

        if not source_str or not new_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Both 'source_path' and 'new_name_or_path' are required.")

        try:
            safe_source = validate_safe_storage_path(source_str, must_exist=True)

            # If user passed just a new name (e.g. "updated_report.docx")
            if "/" not in new_path_str and "\\" not in new_path_str:
                safe_dest = safe_source.parent / new_path_str
            else:
                safe_dest = validate_safe_storage_path(new_path_str, allow_creation_in="storage/artifacts")

            safe_dest = validate_safe_storage_path(str(safe_dest), allow_creation_in=str(safe_source.parent))
            safe_dest.parent.mkdir(parents=True, exist_ok=True)

            safe_source.rename(safe_dest)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "old_path": str(safe_source),
                    "new_path": str(safe_dest),
                    "new_filename": safe_dest.name,
                },
                metadata={"old_path": str(safe_source), "new_path": str(safe_dest)},
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File rename failed: {str(e)}")
