import pytest
from fastapi.testclient import TestClient
from apps.backend.app.main import app
from services.agent.tools.file_tools import FileCreateTool, FileModifyTool
from services.agent.tools.registry import ToolRegistry

client = TestClient(app)


def test_file_create_and_modify_tools():
    """Verify file.create and file.modify tools execute safely within sovereign boundaries."""
    registry = ToolRegistry()
    assert registry.get_tool("file.create") is not None
    assert registry.get_tool("file.modify") is not None

    # 1. Create file
    create_tool = registry.get_tool("file.create")
    import asyncio
    res_create = asyncio.run(create_tool.execute({"file_path": "storage/temp/test_create_checklist.txt", "content": "Initial configuration value = 100\nStatus = PENDING"}))
    assert res_create.success is True
    assert res_create.output["bytes_written"] > 0
    assert "sha256_hash" in res_create.output

    # 2. Modify file
    modify_tool = registry.get_tool("file.modify")
    res_modify = asyncio.run(modify_tool.execute({
        "file_path": "storage/temp/test_create_checklist.txt",
        "replacements": {"PENDING": "VERIFIED"},
        "append_content": "Checksum: OK",
    }))
    assert res_modify.success is True
    assert res_modify.output["modifications_count"] >= 2
    assert len(res_modify.output["change_summary"]) >= 2

    # Verify content on disk
    read_tool = registry.get_tool("file.read")
    res_read = asyncio.run(read_tool.execute({"file_path": "storage/temp/test_create_checklist.txt"}))
    assert res_read.success is True
    assert "Status = VERIFIED" in res_read.output["content"]
    assert "Checksum: OK" in res_read.output["content"]


def test_model_gateway_register_toggle_and_delete():
    """Verify Model Gateway allows registering new open-weight models, toggling, and unregistering."""
    new_model_payload = {
        "name": "deepseek-coder:6.7b",
        "display_name": "DeepSeek Coder 6.7B",
        "provider": "ollama",
        "role": "coding",
        "capabilities": ["python", "code_review"],
        "context_length": 16384,
        "vram_estimate_mb": 4200,
        "enabled": True,
        "description": "Test custom specialist model",
    }

    # 1. Register
    res = client.post("/api/v1/models/register", json=new_model_payload)
    assert res.status_code == 201
    assert res.json()["status"] == "success"

    # 2. Verify in status list
    status_res = client.get("/api/v1/models/status")
    assert status_res.status_code == 200
    model_ids = [m["id"] for m in status_res.json()]
    assert "deepseek-coder:6.7b" in model_ids

    # 3. Toggle enabled
    toggle_res = client.post("/api/v1/models/deepseek-coder:6.7b/toggle?enabled=false")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["enabled"] is False

    # 4. Unregister / Delete
    del_res = client.delete("/api/v1/models/deepseek-coder:6.7b")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 5. Confirm deletion
    status_res2 = client.get("/api/v1/models/status")
    model_ids2 = [m["id"] for m in status_res2.json()]
    assert "deepseek-coder:6.7b" not in model_ids2
