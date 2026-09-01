import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.backend.app.main import app
from services.artifacts.models import (
    ApprovalNoteData,
    GeneratedArtifactRecord,
    PdfReportData,
    PresentationData,
    SpreadsheetData,
)
from services.artifacts.service import ArtifactsService


@pytest.fixture
def artifacts_service(tmp_path):
    return ArtifactsService(storage_dir=str(tmp_path / "artifacts"))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------
# 1. DOCX Approval Note Generation
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_docx_approval_note(artifacts_service):
    data = ApprovalNoteData(
        subject="Approval for Bearing Overhaul of Slurry Pump P-101",
        equipment_tag="P-101",
        operating_unit="Unit 04 CDU-1",
        inspection_date="28-AUG-2026",
    )

    record = await artifacts_service.generate_approval_note(data=data, task_id="TASK_INSPECT_001")

    assert isinstance(record, GeneratedArtifactRecord)
    assert record.type == "docx"
    assert record.task_id == "TASK_INSPECT_001"
    assert record.verification_status == "verified"
    assert "qwen2.5vl:7b" in record.models_used

    # Verify real file exists and is not empty
    file_path = Path(record.file_path)
    assert file_path.exists()
    assert file_path.stat().st_size > 5000  # Real docx binary bundle

    # Verify SHA-256 integrity
    file_bytes = file_path.read_bytes()
    expected_hash = hashlib.sha256(file_bytes).hexdigest()
    assert record.sha256_hash == expected_hash


# ---------------------------------------------------------
# 2. XLSX Spreadsheet Generation
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_xlsx_spreadsheet(artifacts_service):
    data = SpreadsheetData(
        title="MRPL_Vibration_Audit",
        sheets={
            "Readings": {
                "headers": ["Tag", "RMS (mm/s)", "Status"],
                "rows": [["P-101", 4.8, "ALERT"], ["P-102", 2.1, "NORMAL"]],
            }
        },
    )

    record = await artifacts_service.generate_spreadsheet(data=data)

    assert record.type == "xlsx"
    file_path = Path(record.file_path)
    assert file_path.exists()
    assert file_path.stat().st_size > 3000


# ---------------------------------------------------------
# 3. PPTX Presentation Deck Generation
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_pptx_presentation(artifacts_service):
    data = PresentationData(
        title="MRPL Slurry Pump Failure Analysis",
        subtitle="CDU-1 Unit 04 Reliability Assessment",
    )

    record = await artifacts_service.generate_presentation(data=data)

    assert record.type == "pptx"
    file_path = Path(record.file_path)
    assert file_path.exists()
    assert file_path.stat().st_size > 15000


# ---------------------------------------------------------
# 4. PDF Engineering Report Generation
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_pdf_report(artifacts_service):
    data = PdfReportData(
        title="MRPL Autonomous Inspection Summary",
        equipment_tag="P-101",
    )

    record = await artifacts_service.generate_pdf(data=data)

    assert record.type == "pdf"
    file_path = Path(record.file_path)
    assert file_path.exists()
    assert file_path.stat().st_size > 1000

    # Real PDF header magic bytes
    assert file_path.read_bytes().startswith(b"%PDF")


# ---------------------------------------------------------
# 5. REST API Endpoint Tests for Artifact Deliverables
# ---------------------------------------------------------

def test_api_artifact_endpoints_and_download(client):
    # 1. POST /api/v1/artifacts/approval-note
    post_res = client.post("/api/v1/artifacts/approval-note", json={"subject": "Pump P-101 Work Order Approval"})
    assert post_res.status_code == 200
    art_data = post_res.json()
    assert art_data["type"] == "docx"
    art_id = art_data["artifact_id"]

    # 2. GET /api/v1/artifacts
    list_res = client.get("/api/v1/artifacts")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(i["artifact_id"] == art_id for i in items)

    # 3. GET /api/v1/artifacts/{id}
    get_res = client.get(f"/api/v1/artifacts/{art_id}")
    assert get_res.status_code == 200
    assert get_res.json()["artifact_id"] == art_id

    # 4. GET /api/v1/artifacts/{id}/download
    dl_res = client.get(f"/api/v1/artifacts/{art_id}/download")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 5000
    downloaded_hash = hashlib.sha256(dl_res.content).hexdigest()
    assert downloaded_hash == art_data["sha256_hash"]
