from typing import Any, Dict, List, Optional
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission
from services.rag.service import RagService


class KnowledgeSearchTool(BaseTool):
    """Local RAG vector search tool for industrial SOPs, manuals, and API standards."""

    def __init__(self, rag_service: Optional[RagService] = None):
        self.rag_service = rag_service or RagService()

    @property
    def name(self) -> str:
        return "knowledge.search"

    @property
    def description(self) -> str:
        return "Search local organizational knowledge base (SOPs, equipment manuals, API 610/510 standards) for grounded industrial guidelines."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Semantic search query or keywords"},
                "limit": {"type": "integer", "description": "Top-k chunks to retrieve", "default": 3},
            },
            "required": ["query"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "chunks": {"type": "array"},
                "citations": {"type": "array"},
                "assembled_context": {"type": "string"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.KNOWLEDGE_ACCESS]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 3))
        if not query:
            return ToolResult(tool_name=self.name, success=False, error="Query parameter is required.")

        try:
            res = await self.rag_service.search(query=query, top_k=limit)
            
            # Format output for agent consumption
            formatted_chunks = [
                {
                    "chunk_id": c.chunk_id,
                    "document": c.document_name,
                    "page": c.page_number,
                    "section": c.section,
                    "text": c.text,
                    "relevance": c.score,
                }
                for c in res.chunks
            ]

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=formatted_chunks,
                metadata={
                    "query": query,
                    "results_count": len(formatted_chunks),
                    "assembled_context": res.assembled_context,
                    "citations": [c.dict() for c in res.citations],
                },
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"Knowledge retrieval error: {str(e)}")
