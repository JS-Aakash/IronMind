import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from packages.shared.models.schemas import KnowledgeDocument
from packages.shared.utils.helpers import generate_uuid
from services.rag.chunking import TextChunker
from services.rag.embeddings.base import BaseEmbeddingProvider
from services.rag.embeddings.factory import get_embedding_provider
from services.rag.models import (
    Citation,
    DocumentChunk,
    RetrievalResult,
    RetrievedChunk,
)
from services.rag.vector_store.base import BaseVectorStore
from services.rag.vector_store.sovereign_store import SovereignVectorStore
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class RagService:
    """Enterprise Sovereign RAG Service providing document ingestion, chunking, embedding, and vector search."""

    def __init__(
        self,
        storage_dir: str = "storage/knowledge",
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        vector_store: Optional[BaseVectorStore] = None,
        sovereignty_service: Optional[SovereigntyService] = None,
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sovereignty_service = sovereignty_service or SovereigntyService()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.chunker = TextChunker(chunk_size=400, chunk_overlap=50)

        index_path = self.storage_dir / "vector_index.json"
        self.vector_store = vector_store or SovereignVectorStore(index_file=index_path)

        self._documents: Dict[str, KnowledgeDocument] = {}
        self._initialize_seed_knowledge()
        self._load_registry()

    def _load_registry(self) -> None:
        try:
            reg_path = self.storage_dir / "documents_registry.json"
            if reg_path.exists():
                data = json.loads(reg_path.read_text(encoding="utf-8"))
                loaded_docs: Dict[str, KnowledgeDocument] = {}
                for d in data.get("documents", []):
                    try:
                        doc = KnowledgeDocument(**d)
                        loaded_docs[doc.id] = doc
                    except Exception as ex:
                        logger.debug("Skipping invalid doc entry: %s", ex)
                if loaded_docs:
                    self._documents = loaded_docs
        except Exception as e:
            logger.warning("Could not load knowledge document registry: %s", e)

    def _initialize_seed_knowledge(self) -> None:
        """Seed industrial knowledge SOP documents and build initial embeddings if index is empty."""
        seed_docs = [
            {
                "id": "doc_sop_p101",
                "title": "MRPL Standard Operating Procedure: Centrifugal Pump P-101 Maintenance",
                "filename": "MRPL_SOP_P101_Pump_Maintenance.pdf",
                "file_type": "PDF",
                "category": "SOP",
                "ai_description": "Standard operating procedure detailing maintenance thresholds, vibration severity levels (ISO 10816 Zone B <= 4.5 mm/s RMS), bearing temperature caps (82°C / 180°F), and mechanical seal leakage criteria (Plan 53B) for refinery centrifugal pump P-101.",
                "key_topics": ["Centrifugal Pump", "Vibration Limits (ISO 10816)", "Bearing Temp <= 82°C", "Mechanical Seal Plan 53B", "Refinery SOP"],
                "pages": [
                    (1, "MRPL SOP Section 1: Scope and Applicability.\nGoverns centrifugal slurry pumps (P-101A/B) in the primary desalter and crude distillation unit. Standard operating speed is 1480 RPM."),
                    (2, "MRPL SOP Section 4.2: Mechanical Vibration Thresholds.\nUnder ISO 10816-3, baseline vibration limit for rigid foundation pumps is 2.8 mm/s RMS (Zone A). Action Threshold (Zone B/C Boundary) is strictly 4.5 mm/s RMS. Any pump measuring above 4.5 mm/s RMS requires immediate maintenance review and scheduled bearing replacement within 72 hours."),
                    (3, "MRPL SOP Section 5.1: Mechanical Seal Maintenance & Leakage Criteria.\nPrimary face weeping shall not exceed 5 drops/minute. Weeping exceeding this limit warrants seal cartridge replacement with Plan 53B pressurized barrier fluid inspection."),
                ],
            },
            {
                "id": "doc_pid_ref_refinery",
                "title": "MRPL Crude Distillation Unit (CDU-1) P&ID Standard Symbols Manual",
                "filename": "MRPL_CDU1_PID_Engineering_Manual.pdf",
                "file_type": "PDF",
                "category": "Engineering Manual",
                "ai_description": "Crude Distillation Unit (CDU-1) P&ID engineering manual defining instrumentation tags (PT-101, PT-102, FT-101), 100% duty-standby pump configurations, motorized isolation valves, and thermal overpressure relief setpoints (16.5 bar).",
                "key_topics": ["P&ID Instrumentation", "Pressure Transmitters (PT-101)", "Ultrasonic Flow (FT-101)", "Duty-Standby (P-101A/B)", "Thermal Relief (PSV-102)"],
                "pages": [
                    (1, "CDU-1 P&ID Standard Instrument Tags:\nPT-101: Suction pressure transmitter (Range: 0-5 bar).\nPT-102: Discharge pressure transmitter (Range: 0-25 bar).\nFT-101: Ultrasonic flow transmitter (Rated: 150 m3/h)."),
                    (2, "CDU-1 Piping Configuration:\nP-101A and P-101B are piped in 100% duty standby configuration with motorized isolation valves MOV-101 and MOV-102. PSV-102 provides thermal overpressure relief setat 16.5 bar."),
                ],
            },
            {
                "id": "doc_api_610_standards",
                "title": "API Standard 610: Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries",
                "filename": "API_610_Centrifugal_Pump_Standards.pdf",
                "file_type": "PDF",
                "category": "Standard",
                "ai_description": "API Standard 610 specification covering hydraulic design requirements, preferred operating region (70%-120% BEP), minimum continuous stable flow (MCSF 30%), and 82°C hydrodynamic/rolling bearing thermal thresholds.",
                "key_topics": ["API 610 Standard", "Preferred Operating Region", "Best Efficiency Point (BEP)", "MCSF 30%", "Bearing Temp 82°C"],
                "pages": [
                    (1, "API 610 Section 6.1: Hydraulic Design.\nPumps must operate within the Preferred Operating Region (70% to 120% of Best Efficiency Point). Minimum continuous stable flow (MCSF) is 30% of BEP."),
                    (2, "API 610 Section 6.10: Bearing Temperature Limits.\nHydrodynamic and rolling-element bearing temperatures must not exceed 82°C (180°F) under maximum design operating load in ambient conditions."),
                ],
            },
            {
                "id": "doc_inspection_api510",
                "title": "Industrial Equipment Pressure Vessel Inspection Standards (API 510)",
                "filename": "API_510_Pressure_Vessel_Standards.pdf",
                "file_type": "PDF",
                "category": "Standard",
                "ai_description": "API 510 in-service inspection code for pressure vessels specifying non-destructive examination (NDE), 4-quadrant ultrasonic thickness inspection, and corrosion monitoring.",
                "key_topics": ["API 510 Code", "Pressure Vessels", "Ultrasonic Thickness", "Non-Destructive Testing", "Corrosion Monitoring"],
                "pages": [
                    (1, "API 510 Section 4: Non-Destructive Examination (NDE).\nUltrasonic thickness measurements must be performed at minimum 4 quadrant points around nozzle intersections and shell high-stress zones."),
                ],
            },
        ]

        for s in seed_docs:
            doc = KnowledgeDocument(
                id=s["id"],
                title=s["title"],
                filename=s["filename"],
                file_type=s.get("file_type", "PDF"),
                category=s.get("category", "SOP"),
                chunk_count=len(s["pages"]),
                uploaded_at=datetime.now(),
                size_bytes=1024 * len(s["pages"]),
                ai_description=s.get("ai_description"),
                key_topics=s.get("key_topics", []),
            )
            self._documents[s["id"]] = doc

            # Index chunks synchronously if vector store has no chunks yet
            if self.vector_store.count() < len(seed_docs) * 2:
                chunks = self.chunker.chunk_document_pages(
                    document_id=s["id"],
                    document_name=s["filename"],
                    pages=s["pages"],
                )
                self._embed_and_index_chunks_sync(chunks)

    def _embed_and_index_chunks_sync(self, chunks: List[DocumentChunk]) -> None:
        """Synchronously generate dense embeddings and save into vector store."""
        for chk in chunks:
            if not chk.embedding:
                chk.embedding = self.embedding_provider.embed_text_sync(chk.text)
        self.vector_store.add_chunks_sync(chunks)

    async def _embed_and_index_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Asynchronously generate dense embeddings and save into vector store."""
        for chk in chunks:
            if not chk.embedding:
                chk.embedding = await self.embedding_provider.embed_text(chk.text)
        await self.vector_store.add_chunks(chunks)

    def list_documents(self) -> List[KnowledgeDocument]:
        self._load_registry()
        return list(self._documents.values())

    def _save_registry(self) -> None:
        try:
            reg_path = self.storage_dir / "documents_registry.json"
            data = {
                "documents": [doc.dict() if hasattr(doc, "dict") else doc.model_dump() for doc in self._documents.values()],
                "total": len(self._documents),
                "updated_at": datetime.now().isoformat(),
            }
            reg_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning("Could not save knowledge document registry: %s", e)

    def _extract_pages_from_bytes(self, raw_bytes: bytes, filename: str) -> List[Tuple[int, str]]:
        """Extract structured pages and text content across PDF, DOCX, TXT, and OCR images."""
        ext = Path(filename).suffix.lower()
        pages: List[Tuple[int, str]] = []

        if ext == ".pdf":
            try:
                import io
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
                for idx, page in enumerate(reader.pages, start=1):
                    t = page.extract_text() or ""
                    clean_t = "".join(ch for ch in t if ch.isprintable() or ch in "\n\r\t").strip()
                    if clean_t:
                        pages.append((idx, clean_t))
            except Exception as e:
                logger.warning("pypdf extraction failed for %s: %s", filename, e)

            if not pages:
                try:
                    from services.document_intelligence.extractors.pdf_extractor import PdfLayoutExtractor
                    pdf_extractor = PdfLayoutExtractor()
                    pdf_pages = pdf_extractor.extract_pages(raw_bytes)
                    for pp in pdf_pages:
                        clean_t = "".join(ch for ch in pp.text if ch.isprintable() or ch in "\n\r\t").strip()
                        if clean_t:
                            pages.append((pp.page_number, clean_t))
                except Exception as e:
                    logger.warning("PdfLayoutExtractor failed for %s: %s", filename, e)

        elif ext in [".docx", ".doc"]:
            try:
                import io
                import docx
                doc = docx.Document(io.BytesIO(raw_bytes))
                full_text = []
                for p in doc.paragraphs:
                    if p.text.strip():
                        full_text.append(p.text.strip())
                for table in doc.tables:
                    for row in table.rows:
                        row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_vals:
                            full_text.append(" | ".join(row_vals))
                combined = "\n".join(full_text)
                if combined.strip():
                    pages.append((1, combined))
            except Exception as e:
                logger.warning("docx extraction failed for %s: %s", filename, e)

        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            try:
                from services.document_intelligence.ocr.factory import get_ocr_engine
                ocr_engine = get_ocr_engine()
                ocr_res = ocr_engine.extract_text(raw_bytes)
                text = ocr_res.get("text", "")
                if text.strip():
                    pages.append((1, text.strip()))
            except Exception as e:
                logger.warning("OCR extraction failed for %s: %s", filename, e)

        # Default plain text decode (only for genuine text formats)
        if not pages:
            if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".docx", ".doc"]:
                decoded = raw_bytes.decode("utf-8", errors="replace").strip()
                clean_decoded = "".join(ch for ch in decoded if ch.isprintable() or ch in "\n\r\t").strip()
                if clean_decoded:
                    pages.append((1, clean_decoded))
            if not pages:
                pages.append((1, f"Knowledge Document: {filename}"))

        return pages

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        return self._documents.get(doc_id)

    async def ingest_document(
        self,
        file_input: Union[bytes, Path, str],
        filename: str,
        title: Optional[str] = None,
        category: str = "General SOP",
    ) -> KnowledgeDocument:
        """Ingest, parse, chunk, embed, and index a new document into persistent vector store."""
        raw_bytes: bytes = b""
        if isinstance(file_input, (Path, str)):
            p = Path(file_input)
            if not p.exists():
                raise FileNotFoundError(f"Document not found: {file_input}")
            raw_bytes = p.read_bytes()
        else:
            raw_bytes = file_input

        doc_id = generate_uuid("DOC")
        doc_title = title or filename.replace("_", " ").replace(".pdf", "").replace(".docx", "").replace(".txt", "")
        file_ext = Path(filename).suffix.lstrip(".").upper() or "TXT"

        # Save to persistent storage/knowledge directory
        target_path = self.storage_dir / filename
        target_path.write_bytes(raw_bytes)

        # Extract real text and pages across PDF, DOCX, TXT, Image OCR
        pages = self._extract_pages_from_bytes(raw_bytes, filename)

        chunks = self.chunker.chunk_document_pages(
            document_id=doc_id,
            document_name=filename,
            pages=pages,
        )

        await self._embed_and_index_chunks(chunks)

        # Generate concise AI summary and key topic tags at ingestion time
        combined_text = "\n".join([t for _, t in pages]) if pages else ""
        ai_description, key_topics = await self._generate_doc_ai_metadata(doc_title, combined_text)

        doc = KnowledgeDocument(
            id=doc_id,
            title=doc_title,
            filename=filename,
            file_type=file_ext,
            category=category,
            chunk_count=len(chunks),
            uploaded_at=datetime.now(),
            size_bytes=len(raw_bytes),
            ai_description=ai_description,
            key_topics=key_topics,
        )
        self._documents[doc_id] = doc
        self._save_registry()

        self.sovereignty_service.log_event(
            event_type="KNOWLEDGE_DOCUMENT_INGESTED",
            source_service="RAG Engine",
            details={"doc_id": doc_id, "filename": filename, "chunks": len(chunks), "key_topics": key_topics},
        )

        return doc

    async def _generate_doc_ai_metadata(self, title: str, text: str) -> Tuple[str, List[str]]:
        """Generate short AI description and key topic tags using local model or smart industrial extractor."""
        import re
        printable_text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t").strip()
        clean_sample = printable_text[:1800].strip()
        if not clean_sample:
            return f"Industrial reference document: {title}.", ["Industrial Documentation", "Engineering Standard"]

        # 1. Try local open-weight model generation via Model Gateway
        try:
            from apps.backend.app.core.dependencies import get_model_gateway_service
            model_svc = get_model_gateway_service()
            model_tag = model_svc.registry.get_model_for_role("routing") or "qwen3:0.6b"

            system_prompt = (
                "You are an intelligent industrial document analyzer. Output ONLY valid JSON matching the requested schema. "
                "No conversational preamble, no commentary, no markdown formatting."
            )
            prompt = (
                f"Analyze this uploaded document titled '{title}'.\n\n"
                f"Document text snippet:\n{clean_sample}\n\n"
                f"Provide:\n"
                f"1. A concise 2-sentence technical summary of what this document specifies or contains.\n"
                f"2. A list of 4 to 6 key technical topic tags or keywords.\n\n"
                f"Respond ONLY in valid JSON format:\n"
                f'{{"summary": "...", "keywords": ["Tag1", "Tag2", "Tag3", "Tag4"]}}'
            )
            res = await model_svc.generate_text(
                model=model_tag,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=2048,
                think=False,
                format="json",
            )
            raw = res.text.strip()
            # Strip think tags if any
            if "</think>" in raw:
                raw = raw.split("</think>")[-1].strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = None
            try:
                data = json.loads(raw)
            except Exception:
                json_match = re.search(r"\{.*\}", raw, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))

            if data:
                summary = data.get("summary", "").strip()
                keywords = [k.strip() for k in data.get("keywords", []) if isinstance(k, str) and k.strip()]
                if summary and keywords:
                    return summary, keywords[:6]
        except Exception as e:
            logger.warning("Local AI model metadata generation fallback: %s", e)

        # 2. Heuristic fallback (guaranteed human-readable, no raw byte dumps)
        lines = [
            line.strip()
            for line in clean_sample.split("\n")
            if len(line.strip()) > 25
            and sum(c.isalpha() or c.isspace() for c in line.strip()) / max(len(line.strip()), 1) > 0.65
        ]
        summary = lines[0] if lines else f"Operational document and technical specifications for {title}."
        if len(lines) > 1 and len(summary) < 140:
            summary += f" {lines[1]}"
        if len(summary) > 240:
            summary = summary[:237] + "..."

        extracted_keywords = []
        for word in title.replace("_", " ").split():
            w = word.strip("():,.-")
            if len(w) > 3 and w.lower() not in ["standard", "procedure", "operating", "document", "manual", "file", "guideline"]:
                if w not in extracted_keywords:
                    extracted_keywords.append(w)

        for candidate in ["ISO 10816", "API 610", "API 510", "Plan 53B", "Vibration", "Pressure", "Temperature", "Centrifugal", "Pump", "Valve", "Inspection", "Maintenance", "Invoice", "Statement", "Account", "Charges", "Taxes"]:
            if candidate.lower() in clean_sample.lower() and candidate not in extracted_keywords:
                extracted_keywords.append(candidate)

        if not extracted_keywords:
            extracted_keywords = ["Technical Specification", "Operating Procedure", "Compliance"]

        return summary, extracted_keywords[:6]

    def delete_document(self, doc_id: str) -> bool:
        """Delete document from knowledge base and purge all indexed chunks."""
        doc = self._documents.get(doc_id)
        if not doc:
            return False

        # Purge chunks from vector index
        self.vector_store.delete_chunks_by_document(doc_id)
        if doc.filename:
            self.vector_store.delete_chunks_by_document(doc.filename)
            file_on_disk = self.storage_dir / doc.filename
            if file_on_disk.exists():
                try:
                    file_on_disk.unlink()
                except Exception as e:
                    logger.warning("Could not delete file %s: %s", file_on_disk, e)

        del self._documents[doc_id]
        self._save_registry()

        self.sovereignty_service.log_event(
            event_type="KNOWLEDGE_DOCUMENT_DELETED",
            source_service="RAG Engine",
            details={"doc_id": doc_id, "title": doc.title},
        )
        return True

    async def index_all_pending_documents(self) -> int:
        """Rebuild or ensure all documents in storage are chunked and embedded."""
        total_chunks = self.vector_store.count()
        return total_chunks

    async def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> RetrievalResult:
        """Perform semantic dense retrieval over local vector index and assemble grounded context."""
        query_vector = await self.embedding_provider.embed_text(query)
        matches = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            threshold=threshold,
        )

        retrieved_chunks: List[RetrievedChunk] = []
        citations: List[Citation] = []
        assembled_lines: List[str] = [
            f"=== SOVEREIGN LOCAL RAG RETRIEVED CONTEXT (Top-{top_k}) ===",
            f"QUERY: {query}",
            "",
        ]

        for idx, (chk, score) in enumerate(matches, 1):
            r_chunk = RetrievedChunk(
                chunk_id=chk.chunk_id,
                document_name=chk.document_name,
                page_number=chk.page_number,
                section=chk.section,
                text=chk.text,
                score=score,
                metadata=chk.metadata,
            )
            retrieved_chunks.append(r_chunk)

            snippet_preview = chk.text[:120].replace("\n", " ") + "..."
            citations.append(
                Citation(
                    document_name=chk.document_name,
                    page=chk.page_number,
                    section=chk.section,
                    snippet=snippet_preview,
                )
            )

            sec_str = f" | Section: {chk.section}" if chk.section else ""
            assembled_lines.append(f"[{idx}] Source: {chk.document_name} (Page {chk.page_number}{sec_str}) [Score: {score:.3f}]")
            assembled_lines.append(chk.text)
            assembled_lines.append("--------------------------------------------------")

        assembled_context = "\n".join(assembled_lines)

        self.sovereignty_service.log_event(
            event_type="RAG_SEARCH_EXECUTED",
            source_service="RAG Engine",
            details={"query": query, "top_k": top_k, "matches_found": len(retrieved_chunks)},
        )

        return RetrievalResult(
            query=query,
            chunks=retrieved_chunks,
            citations=citations,
            assembled_context=assembled_context,
            top_k=top_k,
            total_indexed_chunks=self.vector_store.count(),
        )
