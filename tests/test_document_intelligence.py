import io
import pytest
from fastapi.testclient import TestClient

from apps.backend.app.main import app
from services.document_intelligence.models import NormalizedDocument
from services.document_intelligence.pipeline import UnsupportedFileFormatError
from services.document_intelligence.service import DocumentIntelligenceService


@pytest.fixture
def doc_service():
    return DocumentIntelligenceService()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------
# 1. Image OCR & Multimodal Document Intelligence
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_process_inspection_image(doc_service):
    # Simulated scanned inspection report image payload
    sample_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03\x20\x00\x00\x02X\x08\x06\x00\x00\x00"

    doc = await doc_service.process_document(
        file_input=sample_image_bytes,
        filename="pump_p101_vibration_scan.png",
        enable_vision_llm=True,
    )

    assert isinstance(doc, NormalizedDocument)
    assert doc.filename == "pump_p101_vibration_scan.png"
    assert doc.file_type == "png"
    assert doc.total_pages == 1
    assert len(doc.pages) == 1

    # Check OCR & text extraction
    page = doc.pages[0]
    assert page.ocr_applied is True
    assert "MANGALORE REFINERY" in page.raw_text
    assert "P-101" in page.raw_text

    # Check Multimodal Visual Analysis
    assert page.visual_analysis is not None
    assert "P-101" in page.visual_analysis.equipment_tags
    assert len(page.visual_analysis.observed_anomalies) > 0

    # Check Local Persistence
    retrieved = doc_service.get_document(doc.document_id)
    assert retrieved is not None
    assert retrieved.document_id == doc.document_id


# ---------------------------------------------------------
# 2. PDF Document Layout & Table Extraction
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_process_pdf_with_tables(doc_service):
    sample_pdf_text = (
        "MANGALORE REFINERY AND PETROCHEMICALS LIMITED\n"
        "EQUIPMENT HEALTH AUDIT REPORT - UNIT 04\n\n"
        "| Parameter | Measured | Limit | Status |\n"
        "| Vibration RMS | 4.8 mm/s | 4.5 mm/s | ALERT |\n"
        "| Bearing Temp | 78.5 C | 70.0 C | ALERT |\n"
        "| Discharge Press | 12.4 bar | 14.0 bar | NORMAL |\n\n"
        "Equipment P-101 requires bearing assembly replacement under API 610.\n"
    )

    doc = await doc_service.process_document(
        file_input=sample_pdf_text.encode("utf-8"),
        filename="refinery_audit_report.pdf",
        enable_vision_llm=True,
    )

    assert doc.file_type == "pdf"
    assert doc.total_pages >= 1
    assert len(doc.extracted_tables) >= 1

    table = doc.extracted_tables[0]
    assert "Parameter" in table.headers
    assert len(table.rows) == 3
    assert table.rows[0][0] == "Vibration RMS"
    assert table.rows[0][3] == "ALERT"


# ---------------------------------------------------------
# 3. Unsupported File Format Rejection
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_unsupported_file_format(doc_service):
    with pytest.raises(UnsupportedFileFormatError):
        await doc_service.process_document(
            file_input=b"dummy binary",
            filename="malicious_payload.exe",
        )


# ---------------------------------------------------------
# 4. REST API Endpoint Tests for Document Intelligence
# ---------------------------------------------------------

def test_api_process_document_endpoint(client):
    file_content = (
        "MRPL P&ID SCHEMATIC REVIEW\n"
        "Tag: P-101A/B Slurry Pumps\n"
        "Suction: 2.1 bar, Discharge: 12.4 bar\n"
    )
    files = {"file": ("p101_drawing.pdf", io.BytesIO(file_content.encode("utf-8")), "application/pdf")}
    
    response = client.post("/api/v1/documents/process", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "p101_drawing.pdf"
    assert data["file_type"] == "pdf"
    assert "sha256_hash" in data
    assert "document_id" in data

    # Test GET by ID
    doc_id = data["document_id"]
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["document_id"] == doc_id


def test_api_list_documents(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
