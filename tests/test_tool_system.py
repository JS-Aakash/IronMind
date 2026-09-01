import pytest
from pathlib import Path
from services.agent.tools.registry import ToolRegistry
from services.agent.tools.security import PathTraversalError, validate_safe_storage_path


@pytest.fixture
def registry():
    return ToolRegistry()


# ---------------------------------------------------------
# 1. Valid Tool Execution Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_calculator_tool_valid_math(registry):
    # Arithmetic & constants
    res, rec = await registry.invoke_tool("calculator", {"expression": "150 * 45 * 850 * g / 3.6e6"})
    assert res.success is True
    assert rec.success is True
    assert "result" in res.output
    assert round(res.output["result"], 2) == 15.63

    # Math functions
    res2, _ = await registry.invoke_tool("calculator", {"expression": "sqrt(16) + round(pi, 2) + 2^3"})
    assert res2.success is True
    assert res2.output["result"] == 15.14


@pytest.mark.asyncio
async def test_file_write_and_read_valid(registry):
    test_content = "VIBRATION LOG P-101: 4.8 mm/s RMS"
    filename = "test_audit_vibration.txt"

    # Write file
    w_res, w_rec = await registry.invoke_tool(
        "file.write",
        {"filename": filename, "content": test_content, "target_directory": "storage/temp"},
    )
    assert w_res.success is True
    assert w_rec.success is True

    # Read file
    r_res, r_rec = await registry.invoke_tool(
        "file.read",
        {"file_path": f"storage/temp/{filename}"},
    )
    assert r_res.success is True
    assert test_content in r_res.output["content"]


@pytest.mark.asyncio
async def test_python_execute_valid(registry):
    code = (
        "flow = 150\n"
        "head = 45\n"
        "power = (850 * 9.81 * (flow/3600) * head) / 1000\n"
        "print(f'HYDRAULIC_KW:{power:.2f}')\n"
    )
    res, rec = await registry.invoke_tool("python.execute", {"code": code})
    assert res.success is True
    assert "HYDRAULIC_KW:15.63" in res.output["stdout"]
    assert res.output["exit_code"] == 0


@pytest.mark.asyncio
async def test_document_create_valid(registry):
    res, rec = await registry.invoke_tool(
        "document.create",
        {
            "title": "Slurry Pump Vibration Authorization",
            "equipment_id": "P-101",
            "sections": {
                "Executive Summary": "Vibration levels on bearing housing exceeded 4.5 mm/s limit.",
                "Action Items": ["Issue maintenance overhaul work order", "Replace mechanical seal"],
            },
            "format": "docx",
        },
    )
    assert res.success is True
    assert res.output["verified"] is True
    assert "sha256_hash" in res.output


@pytest.mark.asyncio
async def test_extended_tools_valid(registry):
    # Spreadsheet
    s_res, _ = await registry.invoke_tool(
        "spreadsheet.create",
        {
            "filename": "pump_data.csv",
            "headers": ["Tag", "Flow", "Head", "Status"],
            "rows": [["P-101", 150, 45, "ABNORMAL"], ["P-102", 140, 44, "NORMAL"]],
        },
    )
    assert s_res.success is True

    # Presentation
    p_res, _ = await registry.invoke_tool(
        "presentation.create",
        {
            "title": "Refinery Maintenance Review",
            "slides": [
                {"slide_number": 1, "title": "Overview", "bullet_points": ["Pump P-101 overhaul required"]},
            ],
        },
    )
    assert p_res.success is True

    # PDF
    pdf_res, _ = await registry.invoke_tool(
        "pdf.create",
        {
            "title": "Executive Summary",
            "content_markdown": "Full report generated on-premise.",
            "equipment_tag": "P-101",
        },
    )
    assert pdf_res.success is True


# ---------------------------------------------------------
# 2. Invalid Arguments & Missing Parameters
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_required_arguments(registry):
    # Missing 'expression' in calculator
    res, _ = await registry.invoke_tool("calculator", {})
    assert res.success is False
    assert "Missing required parameter" in res.error

    # Missing 'code' in python.execute
    res2, _ = await registry.invoke_tool("python.execute", {})
    assert res2.success is False
    assert "Missing required parameter" in res2.error

    # Missing 'file_path' in file.read
    res3, _ = await registry.invoke_tool("file.read", {})
    assert res3.success is False
    assert "Missing required parameter" in res3.error


# ---------------------------------------------------------
# 3. Path Traversal & Unauthorized Access Defense
# ---------------------------------------------------------

def test_path_traversal_prevention():
    # Attempting to read outside storage
    with pytest.raises(PathTraversalError):
        validate_safe_storage_path("../../.env")

    with pytest.raises(PathTraversalError):
        validate_safe_storage_path("../../../etc/passwd")

    with pytest.raises(PathTraversalError):
        validate_safe_storage_path("storage/uploads/../../secret.key")

    with pytest.raises(PathTraversalError):
        validate_safe_storage_path("C:\\Windows\\System32\\cmd.exe")

    with pytest.raises(PathTraversalError):
        validate_safe_storage_path("storage/uploads/test.txt\0.exe")


@pytest.mark.asyncio
async def test_file_tools_path_traversal_attack(registry):
    # Attempting path traversal in file.read
    res, _ = await registry.invoke_tool("file.read", {"file_path": "../../.env"})
    assert res.success is False
    assert "Security violation" in res.error or "Path traversal" in res.error

    # Attempting path traversal in file.write
    res2, _ = await registry.invoke_tool(
        "file.write",
        {"filename": "../../malicious.py", "content": "print('attack')"},
    )
    assert res2.success is False
    assert "Security violation" in res2.error or "Path traversal" in res2.error


# ---------------------------------------------------------
# 4. Security: Forbidden Shell Execution Patterns
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_forbidden_shell_execution_blocked(registry):
    # Attempting to pass shell commands through generic tool arguments
    res, _ = await registry.invoke_tool("file.read", {"file_path": "storage/uploads/file.txt; os.system('whoami')"})
    assert res.success is False
    assert "Security Policy Violation" in res.error

    res2, _ = await registry.invoke_tool("calculator", {"expression": "subprocess.Popen('cmd.exe')"})
    assert res2.success is False
    assert "Security Policy Violation" in res2.error


# ---------------------------------------------------------
# 5. Tool Failure Handling & Explicit Errors
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_calculator_division_by_zero(registry):
    res, _ = await registry.invoke_tool("calculator", {"expression": "100 / 0"})
    assert res.success is False
    assert "Division by zero" in res.error


@pytest.mark.asyncio
async def test_python_execute_runtime_error(registry):
    # Python code with intentional assertion failure / syntax error
    failing_code = "x = 10\nassert x == 20, 'Assertion Failed in Sandbox'\n"
    res, _ = await registry.invoke_tool("python.execute", {"code": failing_code})
    assert res.success is False
    assert "AssertionError" in res.error or "non-zero code" in res.error


@pytest.mark.asyncio
async def test_unknown_tool_invocation(registry):
    res, _ = await registry.invoke_tool("arbitrary.dangerous_tool", {"action": "destroy"})
    assert res.success is False
    assert "not registered" in res.error


# ---------------------------------------------------------
# 6. REST API Endpoint Tests for Tools
# ---------------------------------------------------------

from fastapi.testclient import TestClient
from apps.backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_api_list_tools(client):
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    names = [t["name"] for t in data]
    assert "calculator" in names
    assert "file.read" in names
    assert "file.write" in names
    assert "python.execute" in names
    assert "document.create" in names


def test_api_invoke_calculator_tool(client):
    payload = {
        "tool_name": "calculator",
        "arguments": {"expression": "25 * 4 + sqrt(144)"},
    }
    response = client.post("/api/v1/tools/invoke", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["output"]["result"] == 112

