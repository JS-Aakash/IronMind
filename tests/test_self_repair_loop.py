import pytest
from unittest.mock import AsyncMock, MagicMock
from services.agent.orchestrator import AgentOrchestrator
from services.model_gateway.service import ModelService
from services.model_gateway.registry import ModelRegistry
from services.model_gateway.providers.mock import MockProvider
from services.agent.state import AgentState, AgentStatus, PlanStep
from services.model_gateway.router_models import TaskType

@pytest.mark.asyncio
async def test_sandbox_self_repair_on_assertion_failure():
    model_registry = ModelRegistry()
    mock_provider = MockProvider()
    model_svc = ModelService(registry=model_registry)
    model_svc.register_provider(mock_provider)

    orchestrator = AgentOrchestrator(model_service=model_svc)

    state = AgentState(
        task_id="TEST_REPAIR_01",
        user_goal="Calculate pump efficiency with assertion",
        task_type=TaskType.CODING,
        status=AgentStatus.EXECUTING,
    )

    # Broken code with assertion failure
    broken_code = "assert 10 == 20, 'Mathematical contradiction'"
    fixed_code = "assert 20 == 20, 'Corrected'\nprint('PUMP_EFFICIENCY_VERIFIED_78.4%')"

    # Mock the LLM to return error analysis and the corrected code
    mock_gen_resp = MagicMock()
    mock_gen_resp.text = (
        "ROOT_CAUSE: Expected 10 to equal 20 which is an assertion contradiction.\n"
        "FIX: Aligned assertion to test matching values and physical efficiency.\n"
        f"```python\n{fixed_code}\n```"
    )
    model_svc.generate = AsyncMock(return_value=mock_gen_resp)

    # Create step that runs sandbox
    step = PlanStep(
        step_id="step_sandbox_01",
        order=1,
        title="Execute Pump Efficiency Script in Sandbox",
        description="Run isolated python sandbox with assertions",
        assigned_model="qwen2.5-coder:7b",
        tool_name="python.execute_sandbox",
        tool_args={"code": broken_code},
    )

    # Call _execute_step
    success, obs = await orchestrator._execute_step(state, step)

    assert success is True
    # Verify that recovery attempts were recorded
    assert len(state.recovery_attempts) >= 2
    attempt_1 = state.recovery_attempts[0]
    attempt_2 = state.recovery_attempts[1]

    assert attempt_1.attempt_number == 1
    assert attempt_1.status == "failed"
    assert "AssertionError" in str(attempt_1.failure_details)
    assert attempt_1.root_cause_analysis is not None
    assert attempt_1.fix_description is not None

    assert attempt_2.attempt_number == 2
    assert attempt_2.status == "verified"
    assert attempt_2.exit_code == 0

    # Check real events emitted in execution trace
    event_types = [e.get("event_type") for e in state.execution_trace]
    assert "ATTEMPT_FAILED" in event_types
    assert "ERROR_ANALYSIS" in event_types
    assert "FIX_APPLIED" in event_types
    assert "ATTEMPT_VERIFIED" in event_types


@pytest.mark.asyncio
async def test_sandbox_unrecoverable_halts_and_prompts_user():
    model_registry = ModelRegistry()
    mock_provider = MockProvider()
    model_svc = ModelService(registry=model_registry)
    model_svc.register_provider(mock_provider)

    orchestrator = AgentOrchestrator(model_service=model_svc)

    state = AgentState(
        task_id="TEST_REPAIR_FATAL",
        user_goal="Attempt forbidden operation",
        task_type=TaskType.CODING,
        status=AgentStatus.EXECUTING,
    )

    # Code that triggers unrecoverable OS permission error simulation
    fatal_code = "raise PermissionError('Permission denied: /etc/shadow access is denied')"

    step = PlanStep(
        step_id="step_sandbox_fatal",
        order=1,
        title="Run System Access in Sandbox",
        description="Attempt unauthorized file access",
        assigned_model="qwen2.5-coder:7b",
        tool_name="python.execute_sandbox",
        tool_args={"code": fatal_code},
    )

    success, obs = await orchestrator._execute_step(state, step)

    # Execution should halt cleanly without infinite retry loops
    assert success is False
    assert state.status == AgentStatus.HUMAN_REVIEW_REQUIRED
    assert state.user_intervention_prompt is not None
    assert "unrecoverable" in state.user_intervention_prompt.lower()

    # Recovery attempt record marked as halted
    assert len(state.recovery_attempts) >= 1
    assert state.recovery_attempts[0].status == "halted"
    assert state.recovery_attempts[0].is_recoverable is False

    event_types = [e.get("event_type") for e in state.execution_trace]
    assert "RECOVERY_HALTED" in event_types


@pytest.mark.asyncio
async def test_coding_query_pure_code_constraint():
    model_registry = ModelRegistry()
    mock_provider = MockProvider()
    model_svc = ModelService(registry=model_registry)
    model_svc.register_provider(mock_provider)

    orchestrator = AgentOrchestrator(model_service=model_svc)

    state = AgentState(
        task_id="TEST_PURE_CODE",
        user_goal="Write a function to calculate pump efficiency",
        task_type=TaskType.CODING,
        status=AgentStatus.EXECUTING,
    )

    step = PlanStep(
        step_id="step_code_gen",
        order=1,
        title="Generate Python Solution",
        description="Write code for calculation",
        assigned_model="qwen2.5-coder:7b",
        tool_name=None,  # Pure model reasoning/generation step
    )

    # Mock model returning conversational explanation with markdown code block
    async def mock_stream(*args, **kwargs):
        tokens = [
            "Here is the complete solution for pump efficiency.\n",
            "```python\n",
            "def pump_eff(flow, head):\n",
            "    return (flow * head * 9810) / 1000\n\n",
            "assert pump_eff(1, 10) > 0\n",
            "```\n",
            "I hope this helps your engineering team!",
        ]
        for t in tokens:
            chunk = MagicMock()
            chunk.text = t
            yield chunk

    model_svc.stream = mock_stream

    success, obs = await orchestrator._execute_step(state, step)

    assert success is True
    # Observation must contain ONLY the pure code, stripped of pre-amble and post-amble conversational explanations
    assert "Here is the complete solution" not in obs
    assert "I hope this helps" not in obs
    assert "def pump_eff(flow, head):" in obs
    assert obs.startswith("```python")

