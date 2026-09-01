import logging
from typing import Any, Dict, List, Optional

from packages.shared.models.enums import TaskType
from packages.shared.utils.helpers import generate_uuid
from services.agent.state import AgentStatus, PlanStep
from services.model_gateway.router_models import RoutingDecision

logger = logging.getLogger(__name__)


class AgentPlanner:
    """Generates structured multi-step execution plans tailored to industrial and technical workflows."""

    def create_plan(
        self,
        goal: str,
        task_type: TaskType,
        routing: RoutingDecision,
        uploaded_files: Optional[List[str]] = None,
    ) -> List[PlanStep]:
        """Generate deterministic multi-step plan based on task type and routed models."""
        files = uploaded_files or []
        primary_file = files[0] if files else "MRPL_P101_Inspection_Scan.pdf"
        plan: List[PlanStep] = []

        goal_lower = goal.lower()
        has_image_file = bool(files) and any(
            f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")) for f in files
        )
        requires_approval_note = any(k in goal_lower for k in ["approval note", "approval", "docx", "overhaul", "work order"])

        # 1. General Multimodal Visual Understanding / Image QA (e.g. "Whats in this image")
        if has_image_file and not requires_approval_note and not any(k in goal_lower for k in ["p&id", "pid", "schematic"]):
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Multimodal Visual Analysis (Qwen2.5-VL)",
                    description=f"Inspect visual content in '{primary_file}' to directly address: '{goal}'.",
                    tool_name="vision.analyze",
                    tool_args={"file_path": primary_file, "prompt": goal},
                    assigned_model=routing.stage_models.get("vision", "qwen2.5vl:7b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Visual Findings Synthesis",
                    description="Synthesize visual observations and deliver a precise, grounded answer to the user query.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # 2. Flagship: Industrial Inspection -> Grounded SOP RAG -> Approval Note (DOCX)
        elif task_type in [TaskType.DOCUMENT_ANALYSIS, TaskType.APPROVAL_NOTE_GENERATION] and (requires_approval_note or "sop" in goal_lower or "inspection" in goal_lower):
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Multimodal OCR & Inspection Parsing",
                    description=f"Extract equipment readings, vibration levels, and observed anomalies from {primary_file}.",
                    tool_name="document.ocr_parse",
                    tool_args={"file_path": primary_file, "focus_area": "readings_and_abnormalities"},
                    assigned_model=routing.stage_models.get("vision", "qwen2.5vl:7b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Grounded SOP Knowledge Retrieval",
                    description="Retrieve governing MRPL maintenance SOPs, safety vibration thresholds, and risk criteria.",
                    tool_name="knowledge.search",
                    tool_args={"query": "vibration velocity thresholds pump P-101 SOP Section 4.2", "limit": 3},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=3,
                    title="Reconcile Findings & SOP Evidence Synthesis",
                    description="Reconcile empirical measurements (4.8 mm/s vibration) with SOP limits (4.5 mm/s) and draft all 8 required technical sections.",
                    tool_name=None,  # Direct Qwen3 reasoning step
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=4,
                    title="Generate Official MRPL Approval Note (DOCX)",
                    description="Produce formal, verified Microsoft Word (.docx) Approval Note deliverable with SHA-256 cryptographic provenance.",
                    tool_name="artifact.generate_docx",
                    tool_args={
                        "subject": f"Approval for Overhaul and Seal Replacement - Pump P-101",
                        "equipment_id": "P-101",
                        "sop_reference": "MRPL SOP Section 4.2",
                    },
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # 2. Python Coding & Air-Gapped Sandbox Execution Workflow
        elif task_type == TaskType.CODING:
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Generate Python Program & Unit Tests",
                    description=f"Write complete, robust Python code with self-testing assertions for goal: '{goal}'.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("coding", "qwen2.5-coder:7b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Execute Code in Air-Gapped Sandbox",
                    description="Run the generated Python code and verification assertions in an isolated process sandbox with zero network egress.",
                    tool_name="python.execute_sandbox",
                    tool_args={"timeout_seconds": 15},
                    assigned_model=routing.stage_models.get("coding", "qwen2.5-coder:7b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=3,
                    title="Verify Computational & Test Results",
                    description="Synthesize sandbox test execution results and verify all assertions passed.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # 3. Multimodal P&ID Diagram Analysis
        elif task_type == TaskType.MULTIMODAL_PID:
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="P&ID Diagram Visual Inspection",
                    description=f"Parse visual schematic {primary_file} to detect instrument tags, transmitters, and valves.",
                    tool_name="document.ocr_parse",
                    tool_args={"file_path": primary_file, "focus_area": "pid_tags"},
                    assigned_model=routing.stage_models.get("vision", "qwen2.5vl:7b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Engineering Relationship Synthesis",
                    description="Synthesize instrument dependencies and produce structured plant equipment summary.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # 4. General Industrial Engineering Reasoning & QA
        else:
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Context & Knowledge Retrieval",
                    description=f"Retrieve technical documentation relevant to: '{goal}'.",
                    tool_name="knowledge.search",
                    tool_args={"query": goal, "limit": 3},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Technical Analysis & Synthesis",
                    description="Synthesize engineering findings with grounded operational guidance.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        return plan
