import io
import pytest
from fastapi.testclient import TestClient
from apps.backend.app.main import app

client = TestClient(app)


def test_knowledge_base_upload_and_delete_lifecycle():
    """Verify persistent Knowledge Base upload, indexing, dense search, and deletion."""
    # 1. Upload a new SOP document
    sop_content = b"MRPL Hydrocracker SOP Section 9.1: Reactor feed temperature must remain between 380C and 410C with pressure at 145 bar."
    files = {
        "file": ("MRPL_Hydrocracker_SOP_9_1.txt", io.BytesIO(sop_content), "text/plain"),
    }
    data = {
        "title": "MRPL Hydrocracker Operating Guide",
        "category": "Standard Operating Procedure (SOP)",
    }
    res = client.post("/api/v1/knowledge/upload", files=files, data=data)
    assert res.status_code == 200, res.text
    doc_info = res.json()
    assert doc_info["title"] == "MRPL Hydrocracker Operating Guide"
    assert doc_info["chunk_count"] >= 1
    doc_id = doc_info["id"]

    # 2. Verify it is searchable via dense RAG
    search_res = client.post(
        "/api/v1/knowledge/search",
        json={"query": "Hydrocracker reactor feed temperature and pressure limits", "top_k": 3},
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert any("Hydrocracker" in c["text"] or "380C" in c["text"] for c in search_data["chunks"])

    # 3. Delete the document and purge chunks
    del_res = client.delete(f"/api/v1/knowledge/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # 4. Verify document is removed from document listing
    list_res = client.get("/api/v1/knowledge/documents")
    assert list_res.status_code == 200
    active_ids = [d["id"] for d in list_res.json()]
    assert doc_id not in active_ids


def test_task_file_upload_isolation():
    """Verify task attachment staging does NOT enter the persistent RAG knowledge base."""
    # 1. Upload temporary file specifically for task execution
    task_file_content = b"VIBRATION REPORT: Pump P-205 drive-end RMS 5.2 mm/s."
    files = {
        "file": ("task_pump_205_vibration.txt", io.BytesIO(task_file_content), "text/plain"),
    }
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 200
    staged = upload_res.json()
    assert staged["filename"] == "task_pump_205_vibration.txt"
    assert staged["status"] == "staged_for_task"

    # 2. Confirm it was NOT added to Knowledge Base documents
    kb_res = client.get("/api/v1/knowledge/documents")
    assert kb_res.status_code == 200
    kb_filenames = [d["filename"] for d in kb_res.json()]
    assert "task_pump_205_vibration.txt" not in kb_filenames


def test_general_image_query_multimodal_vision_routing():
    """Verify querying 'Whats in this image' with a photo routes to vision.analyze without creating irrelevant pump DOCX."""
    # 1. Create task with image attachment and general question
    task_res = client.post(
        "/api/v1/tasks",
        json={
            "goal": "Whats in this image",
            "uploaded_files": ["sample_photo.jpg"],
        },
    )
    assert task_res.status_code == 200
    task = task_res.json()
    task_id = task["task_id"]

    # 2. Execute task
    exec_res = client.post(f"/api/v1/tasks/{task_id}/execute", json={"uploaded_files": ["sample_photo.jpg"]})
    assert exec_res.status_code == 200
    result = exec_res.json()

    # 3. Assert plan uses vision.analyze with Qwen2.5-VL and did NOT create an irrelevant approval note
    assert result["status"] == "completed"
    tool_names = [t["tool_name"] for t in result["tool_calls"]]
    assert "vision.analyze" in tool_names
    assert "artifact.generate_docx" not in tool_names
    assert len(result["retrieved_context"]) == 0  # No SOP search triggered
