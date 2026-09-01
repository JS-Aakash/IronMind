import io
import pytest
from fastapi.testclient import TestClient

from apps.backend.app.main import app
from services.agent.tools.rag_tools import KnowledgeSearchTool
from services.rag.chunking import TextChunker
from services.rag.embeddings.deterministic_embedding import DeterministicLocalEmbeddingProvider
from services.rag.models import RetrievalResult
from services.rag.service import RagService
from services.rag.vector_store.sovereign_store import SovereignVectorStore


@pytest.fixture
def rag_service():
    return RagService(storage_dir="storage/knowledge")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------
# 1. Text Chunking & Provenance Tracking
# ---------------------------------------------------------

def test_text_chunker_provenance():
    chunker = TextChunker(chunk_size=200, chunk_overlap=30)
    pages = [
        (1, "MRPL Section 1: Overview\nThis SOP covers Slurry Pump P-101 in CDU-1."),
        (2, "MRPL Section 4.2: Vibration Criteria\nOverall vibration must not exceed 4.5 mm/s RMS under ISO 10816-3. High vibration requires immediate work order."),
    ]
    chunks = chunker.chunk_document_pages("doc_1", "SOP_P101.pdf", pages)

    assert len(chunks) >= 2
    for chk in chunks:
        assert chk.document_name == "SOP_P101.pdf"
        assert chk.page_number in [1, 2]
        assert chk.chunk_id.lower().startswith("chk")
        assert len(chk.text) > 0


# ---------------------------------------------------------
# 2. Embedding Generation & Vector Store Search
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_embedding_and_vector_store():
    embedder = DeterministicLocalEmbeddingProvider()
    store = SovereignVectorStore()

    v1 = await embedder.embed_text("Centrifugal pump vibration limits and bearing maintenance threshold")
    v2 = await embedder.embed_text("Crude distillation column pressure safety valve relief setting")

    assert len(v1) == 384
    assert len(v2) == 384

    # Chunk creation
    chunker = TextChunker()
    chunks = chunker.chunk_document_pages(
        "doc_test",
        "Test_SOP.pdf",
        [(1, "Centrifugal pump P-101 vibration threshold is 4.5 mm/s RMS.")],
    )
    chunks[0].embedding = v1
    store.add_chunks_sync(chunks)

    # Search with query
    query_vec = await embedder.embed_text("vibration limits and bearing maintenance threshold")
    matches = store.search_sync(query_vec, top_k=1)

    assert len(matches) == 1
    matched_chk, score = matches[0]
    assert matched_chk.document_name == "Test_SOP.pdf"
    assert "4.5 mm/s" in matched_chk.text
    assert score > 0.4


# ---------------------------------------------------------
# 3. Top-k Retrieval, Assembled Context & Citations
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_rag_service_search_with_citations(rag_service):
    # Search for vibration criteria
    result = await rag_service.search(query="vibration threshold pump P-101", top_k=2)

    assert isinstance(result, RetrievalResult)
    assert len(result.chunks) > 0
    assert len(result.citations) > 0
    assert "=== SOVEREIGN LOCAL RAG RETRIEVED CONTEXT" in result.assembled_context

    top_chunk = result.chunks[0]
    assert top_chunk.page_number >= 1
    assert "document_name" in top_chunk.dict()
    assert top_chunk.score > 0.0

    # Ensure citation has snippet and page
    top_citation = result.citations[0]
    assert top_citation.page >= 1
    assert len(top_citation.snippet) > 0


# ---------------------------------------------------------
# 4. Custom Document Ingestion
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_ingest_custom_knowledge_document(rag_service):
    sample_text = (
        "MRPL SAFETY STANDARD: EMERGENCY SHUTDOWN VALVES (ESD-101)\n"
        "ESD-101 must close within 2.5 seconds upon activation of High-High Pressure Alarm (PAHH-101).\n"
    )
    doc = await rag_service.ingest_document(
        file_input=sample_text.encode("utf-8"),
        filename="MRPL_ESD101_Safety_Standard.txt",
        title="MRPL ESD-101 Valve Safety Standard",
        category="Safety Standard",
    )

    assert doc.id.lower().startswith("doc")
    assert doc.chunk_count >= 1

    # Search for newly indexed document
    search_res = await rag_service.search("ESD-101 closing time pressure alarm", top_k=1)
    assert len(search_res.chunks) >= 1
    assert "ESD-101" in search_res.chunks[0].text


# ---------------------------------------------------------
# 5. Tool Integration: knowledge.search
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_knowledge_search_tool_integration(rag_service):
    tool = KnowledgeSearchTool(rag_service=rag_service)
    res = await tool.execute({"query": "API 610 bearing temperature limit", "limit": 2})

    assert res.success is True
    assert isinstance(res.output, list)
    assert len(res.output) > 0
    assert "relevance" in res.output[0]
    assert "document" in res.output[0]


# ---------------------------------------------------------
# 6. REST API Endpoint Tests for Local RAG
# ---------------------------------------------------------

def test_api_knowledge_endpoints(client):
    # 1. GET /api/v1/knowledge/documents
    list_res = client.get("/api/v1/knowledge/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert isinstance(docs, list)
    assert len(docs) >= 3

    # 2. POST /api/v1/knowledge/upload
    file_bytes = b"MRPL REFINERY FLARING SYSTEM MANUAL\nMaximum smokeless flaring rate is 120 tons/hour.\n"
    files = {"file": ("MRPL_Flaring_Manual.txt", io.BytesIO(file_bytes), "text/plain")}
    data = {"title": "MRPL Flaring Manual", "category": "Environmental Standard"}
    upload_res = client.post("/api/v1/knowledge/upload", files=files, data=data)
    assert upload_res.status_code == 200
    uploaded_doc = upload_res.json()
    assert uploaded_doc["filename"] == "MRPL_Flaring_Manual.txt"

    # 3. POST /api/v1/knowledge/index
    index_res = client.post("/api/v1/knowledge/index", json={"rebuild_embeddings": False})
    assert index_res.status_code == 200
    assert index_res.json()["status"] == "indexed"

    # 4. POST /api/v1/knowledge/search
    search_payload = {"query": "smokeless flaring rate", "top_k": 2}
    search_res = client.post("/api/v1/knowledge/search", json=search_payload)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["chunks"]) >= 1
    assert "citations" in search_data
