import pytest
import asyncio
from pathlib import Path
from services.agent.tools.vision_tools import PidAnalyzeTool
from services.agent.tools.registry import ToolRegistry
from services.agent.planner import AgentPlanner
from services.model_gateway.router_models import RoutingDecision, TaskType
from services.sovereignty.service import SovereigntyService

from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_pid_analyze_tool_execution():
    tool = PidAnalyzeTool()
    assert tool.name == "vision.pid_analyze"
    assert "file_path" in tool.input_schema["properties"]

    # Mock analyze_image to avoid waiting for local LLM loading during unit tests
    mock_resp = MagicMock()
    mock_resp.text = "Identified P-101A/B crude pumps, T-101 column, and PT-101 transmitter."
    tool.model_service.analyze_image = AsyncMock(return_value=mock_resp)

    # Execute with test P&ID drawing
    res = await tool.execute({"file_path": "MRPL_Crude_Distillation_P101_PID.png"})
    assert res.success is True
    assert "equipment" in res.output
    assert "instruments" in res.output
    assert "lines" in res.output
    assert "interlocks" in res.output

    equipment = res.output["equipment"]
    assert len(equipment) >= 4
    tags = [e["tag"] for e in equipment]
    assert "P-101A" in tags
    assert "T-101" in tags

    instruments = res.output["instruments"]
    assert len(instruments) >= 4
    inst_tags = [i["tag"] for i in instruments]
    assert "PT-101" in inst_tags
    assert "FT-101" in inst_tags

@pytest.mark.asyncio
async def test_tool_registry_contains_pid_tool():
    registry = ToolRegistry()
    pid_tool = registry.get_tool("vision.pid_analyze")
    assert pid_tool is not None
    assert isinstance(pid_tool, PidAnalyzeTool)

def test_planner_routes_pid_task():
    planner = AgentPlanner()
    routing = RoutingDecision(
        task_type=TaskType.GENERAL_REASONING,
        primary_model="qwen2.5vl:7b",
        stage_models={"vision": "qwen2.5vl:7b", "reasoning": "qwen3:8b"},
        confidence_score=0.95,
        routing_reason="P&ID engineering drawing analysis",
        required_capabilities=["vision"],
        selected_model="qwen2.5vl:7b",
    )
    plan = planner.create_plan(
        goal="Analyze the attached P&ID engineering drawing for MRPL Crude Distillation Unit 01. Extract all ISA-5.1 equipment tags.",
        task_type=TaskType.GENERAL_REASONING,
        routing=routing,
        uploaded_files=["MRPL_Crude_Distillation_P101_PID.png"],
    )
    assert len(plan) >= 2
    step_1 = plan[0]
    assert step_1.tool_name == "vision.pid_analyze"
    assert step_1.assigned_model == "qwen2.5vl:7b"

def test_sovereignty_live_network_audit():
    svc = SovereigntyService()
    audit = svc.get_live_network_audit()

    assert audit["status"] == "AIRGAPPED_VERIFIED"
    assert audit["airgap_mode"] == "ENFORCED"
    assert audit["external_egress_connections"] == 0
    assert audit["external_egress_bytes"] == 0
    assert audit["monitored_loopback_sockets"] >= 0
    assert len(audit["attestation_signature_sha256"]) == 64
    assert len(audit["packet_audit_stream"]) > 0

    # Ensure all inspected sockets verdict is VERIFIED LOOPBACK
    for s in audit["active_sockets"]:
        assert s["verdict"] in ["VERIFIED LOOPBACK", "INTERNAL_IPC_VERIFIED"]
