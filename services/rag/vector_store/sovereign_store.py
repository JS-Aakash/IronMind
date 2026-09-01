import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from services.rag.models import DocumentChunk
from services.rag.vector_store.base import BaseVectorStore

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag1 * mag2)))


class SovereignVectorStore(BaseVectorStore):
    """Local, zero-dependency high-speed vector index with metadata filtering and persistent storage."""

    def __init__(self, index_file: Optional[Path] = None):
        self.index_file = index_file
        self._chunks: Dict[str, DocumentChunk] = {}
        if self.index_file and self.index_file.exists():
            self.load(self.index_file)

    def add_chunks_sync(self, chunks: List[DocumentChunk]) -> None:
        for chk in chunks:
            self._chunks[chk.chunk_id] = chk
        if self.index_file:
            self.save(self.index_file)

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.add_chunks_sync(chunks)

    def search_sync(
        self,
        query_vector: List[float],
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> List[Tuple[DocumentChunk, float]]:
        scored: List[Tuple[DocumentChunk, float]] = []

        for chk in self._chunks.values():
            if not chk.embedding:
                continue
            sim = cosine_similarity(query_vector, chk.embedding)
            if sim >= threshold:
                scored.append((chk, round(sim, 4)))

        # Sort descending by similarity
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> List[Tuple[DocumentChunk, float]]:
        return self.search_sync(query_vector, top_k, threshold)

    def count(self) -> int:
        return len(self._chunks)

    def delete_chunks_by_document(self, document_id: str) -> int:
        """Purge all indexed chunks for a given document from the vector store."""
        to_remove = [
            cid for cid, chk in self._chunks.items()
            if chk.document_id == document_id or chk.document_name == document_id
        ]
        for cid in to_remove:
            del self._chunks[cid]
        if to_remove and self.index_file:
            self.save(self.index_file)
        return len(to_remove)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": [chk.dict() for chk in self._chunks.values()],
            "count": len(self._chunks),
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw.get("chunks", []):
                chk = DocumentChunk(**item)
                self._chunks[chk.chunk_id] = chk
        except Exception as e:
            logger.warning("Could not load vector store from '%s': %s", path, str(e))
