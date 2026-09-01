import re
from typing import List, Optional
from packages.shared.utils.helpers import generate_uuid
from services.rag.models import DocumentChunk


class TextChunker:
    """Intelligent text chunker respecting sentence and paragraph boundaries while tracking source pages and sections."""

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document_pages(
        self,
        document_id: str,
        document_name: str,
        pages: List[tuple[int, str]],  # List of (page_number, text)
    ) -> List[DocumentChunk]:
        """Chunk a document page by page to maintain strict page provenance."""
        all_chunks: List[DocumentChunk] = []

        for page_num, page_text in pages:
            if not page_text or not page_text.strip():
                continue

            page_chunks = self._chunk_single_page(
                document_id=document_id,
                document_name=document_name,
                page_number=page_num,
                text=page_text.strip(),
            )
            all_chunks.extend(page_chunks)

        return all_chunks

    def _chunk_single_page(
        self,
        document_id: str,
        document_name: str,
        page_number: int,
        text: str,
    ) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        paragraphs = text.split("\n\n")

        current_chunk_text = ""
        current_section = None

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Detect section header
            if para.startswith("#") or (len(para) < 60 and ("SECTION" in para.upper() or "CHAPTER" in para.upper() or ":" in para)):
                current_section = para.lstrip("#").strip()

            if len(current_chunk_text) + len(para) <= self.chunk_size:
                current_chunk_text += ("\n\n" + para) if current_chunk_text else para
            else:
                if current_chunk_text:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=generate_uuid("CHK"),
                            document_id=document_id,
                            document_name=document_name,
                            page_number=page_number,
                            section=current_section,
                            text=current_chunk_text.strip(),
                            token_count=len(current_chunk_text.split()),
                            metadata={"char_length": len(current_chunk_text)},
                        )
                    )
                    # Retain overlap from end of current chunk
                    overlap_len = min(len(current_chunk_text), self.chunk_overlap)
                    overlap_text = current_chunk_text[-overlap_len:]
                    current_chunk_text = overlap_text + "\n\n" + para
                else:
                    current_chunk_text = para

        if current_chunk_text.strip():
            chunks.append(
                DocumentChunk(
                    chunk_id=generate_uuid("CHK"),
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page_number,
                    section=current_section,
                    text=current_chunk_text.strip(),
                    token_count=len(current_chunk_text.split()),
                    metadata={"char_length": len(current_chunk_text)},
                )
            )

        return chunks
