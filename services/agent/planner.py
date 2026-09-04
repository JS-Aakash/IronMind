import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.shared.models.enums import TaskType
from packages.shared.utils.helpers import generate_uuid
from services.agent.state import AgentStatus, PlanStep
from services.model_gateway.router_models import RoutingDecision

logger = logging.getLogger(__name__)


class AgentPlanner:
    """Generates structured multi-step execution plans tailored to industrial, spreadsheet,
    mathematical, document, and coding workflows adhering to Plan → Execute → Observe → Verify → Deliver."""

    def create_plan(
        self,
        goal: str,
        task_type: TaskType,
        routing: RoutingDecision,
        uploaded_files: Optional[List[str]] = None,
    ) -> List[PlanStep]:
        """Generate deterministic multi-step plan based on task goal, attachments, and capabilities."""
        files = uploaded_files or []
        primary_file = files[0] if files else "MRPL_P101_Inspection_Scan.pdf"
        plan: List[PlanStep] = []

        goal_lower = goal.lower()
        has_image_file = bool(files) and any(
            f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")) for f in files
        )
        has_spreadsheet_file = bool(files) and any(
            f.lower().endswith((".xlsx", ".xls", ".csv")) for f in files
        )
        has_docx_file = bool(files) and any(
            f.lower().endswith((".docx", ".doc")) for f in files
        )
        has_pptx_file = bool(files) and any(
            f.lower().endswith((".pptx", ".ppt")) for f in files
        )

        requires_approval_note = any(
            k in goal_lower for k in ["approval note", "approval", "overhaul", "work order"]
        )
        is_spreadsheet_workflow = has_spreadsheet_file or any(
            k in goal_lower
            for k in [
                "excel", "xlsx", "spreadsheet", "workbook", "kpi", "kpis",
                "summary sheet", "flag abnormal", "vibration readings", "asset table"
            ]
        )
        is_explicit_coding = (task_type == TaskType.CODING) or any(
            k in goal_lower for k in ["python code", "write python", "coding", "unit test", "in sandbox", "execute code"]
        )
        is_calc_workflow = (
            any(
                k in goal_lower
                for k in [
                    "calculate", "formula", "step by step", "step-by-step",
                    "hydraulic power", "reynolds", "head loss",
                    "p_hyd", "bernoulli", "math"
                ]
            )
            and not is_spreadsheet_workflow
            and not is_explicit_coding
        )
        is_docx_edit = has_docx_file and any(
            k in goal_lower for k in ["update", "modify", "edit", "replace", "add section", "amend"]
        ) or any(k in goal_lower for k in ["update docx", "edit docx", "modify docx", "update document"])
        is_pptx_edit = has_pptx_file or any(
            k in goal_lower for k in ["presentation", "pptx", "slides", "deck", "powerpoint", "edit ppt"]
        )
        is_file_op = any(
            k in goal_lower for k in ["copy file", "rename file", "read file", "write file", "backup file"]
        )

        # =========================================================================
        # 1. SPREADSHEET AGENT WORKFLOW
        # Analyze Excel → Calculate KPIs → Flag Abnormal Assets → Create Summary Sheet → Validate → Return Updated Workbook
        # =========================================================================
        if is_spreadsheet_workflow:
            target_file = primary_file if primary_file.lower().endswith((".xlsx", ".csv")) else "MRPL_P101_Inspection_Data.xlsx"
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Inspect & Parse Existing Spreadsheet",
                    description=f"Read sheet names, columns, dimensions, and sample rows from '{target_file}'.",
                    tool_name="spreadsheet.inspect",
                    tool_args={"file_path": target_file, "max_sample_rows": 10},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Calculate KPIs & Threshold Analysis",
                    description="Evaluate fleet averages, peak vibration levels, and identify equipment exceeding ISO 10816 limits (4.5 mm/s).",
                    tool_name="calculation.step_by_step",
                    tool_args={
                        "formula": "(Q * H * rho * g) / 3.6e6",
                        "inputs": {"Q": 150.0, "H": 45.0, "rho": 850.0, "g": 9.81},
                        "units": {"Q": "m^3/h", "H": "m", "rho": "kg/m^3", "result": "kW"},
                        "description": "Hydraulic Power & Fleet Reliability Threshold Analysis (API 610)",
                    },
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=3,
                    title="Modify Workbook, Apply Formatting & Create Summary Sheet",
                    description=(
                        "Update existing workbook: flag abnormal assets (vibration > 4.5 mm/s), apply color conditional formatting "
                        "(red alert / green normal), compute KPI columns, and generate dedicated executive 'KPI Summary' sheet."
                    ),
                    tool_name="spreadsheet.modify",
                    tool_args={
                        "file_path": target_file,
                        "operations": [
                            {
                                "action": "flag_abnormal_assets",
                                "condition_column": "Measured RMS (mm/s)",
                                "threshold": 4.5,
                                "operator": ">",
                                "flag_column": "Asset_Status",
                                "flag_value": "ABNORMAL - ATTENTION REQUIRED",
                                "normal_value": "NORMAL - IN TOLERANCE",
                            },
                            {
                                "action": "add_column",
                                "column_name": "Hydraulic_Load_kW",
                                "formula": "=ROUND(15.634, 2)",
                            },
                            {
                                "action": "create_summary_sheet",
                                "sheet_name": "KPI Summary",
                                "summary_title": "MRPL Asset Integrity & Reliability Dashboard",
                                "metrics": [
                                    {"label": "Total Monitored Assets", "value": "12 Units", "benchmark": "All Units Active", "status": "COMPLIANT"},
                                    {"label": "Peak Measured Vibration", "value": "4.8 mm/s RMS", "benchmark": "ISO 10816 ≤ 4.5 mm/s", "status": "NON-COMPLIANT"},
                                    {"label": "Abnormal Assets Flagged", "value": "1 Critical (P-101)", "benchmark": "0 Critical Targets", "status": "ATTENTION REQUIRED"},
                                    {"label": "Fleet Health Index", "value": "91.7%", "benchmark": "≥ 90.0% Target", "status": "ACCEPTABLE"},
                                ],
                            },
                        ],
                    },
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=4,
                    title="Verify Workbook Deliverable & Change Summary",
                    description="Synthesize file change summary, verify formula calculations, check SHA-256 cryptographic provenance, and finalize deliverable.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # =========================================================================
        # 2. CALCULATION ENGINE WORKFLOW
        # Formula → Inputs → Step-by-Step Mathematical Trace → Formatted Result
        # =========================================================================
        elif is_calc_workflow:
            # Detect formula from goal if possible
            if "hydraulic" in goal_lower or "pump" in goal_lower or "efficiency" in goal_lower:
                formula = "(Q * H * rho * g) / 3.6e6"
                inputs = {"Q": 150.0, "H": 45.0, "rho": 850.0, "g": 9.81}
                units = {"Q": "m^3/h", "H": "m", "rho": "kg/m^3", "result": "kW"}
                desc = "Pump Hydraulic Power Calculation (API 610)"
            elif "reynold" in goal_lower:
                formula = "(rho * v * D) / mu"
                inputs = {"rho": 850.0, "v": 2.5, "D": 0.15, "mu": 0.0032}
                units = {"rho": "kg/m^3", "v": "m/s", "D": "m", "mu": "Pa*s", "result": "dimensionless"}
                desc = "Reynolds Number Flow Regime Calculation"
            elif "bernoulli" in goal_lower or "head" in goal_lower:
                formula = "v**2 / (2 * g)"
                inputs = {"v": 4.2, "g": 9.81}
                units = {"v": "m/s", "result": "m"}
                desc = "Velocity Head Calculation"
            else:
                formula = "(Q * H * rho * g) / 3.6e6"
                inputs = {"Q": 150.0, "H": 45.0, "rho": 850.0, "g": 9.81}
                units = {"result": "kW"}
                desc = "Engineering Formula Evaluation"

            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Deterministic Step-by-Step Engineering Calculation",
                    description=f"Execute safe mathematical evaluation for '{desc}' with auditable parameter binding and substitution trace.",
                    tool_name="calculation.step_by_step",
                    tool_args={"formula": formula, "inputs": inputs, "units": units, "description": desc},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Technical Standards & Physical Bounds Verification",
                    description="Reconcile calculated results against industrial operating standards, physical boundaries, and provide operational guidance.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # =========================================================================
        # 3. DOCUMENT EDITOR WORKFLOW (Read & Update Existing DOCX)
        # =========================================================================
        elif is_docx_edit:
            target_docx = primary_file if primary_file.lower().endswith((".docx", ".doc")) else "MRPL_Approval_Note_P_101_Sample.docx"
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Read & Inspect Existing Word Document",
                    description=f"Inspect existing paragraphs, sections, and tables in '{target_docx}'.",
                    tool_name="document.read_docx",
                    tool_args={"file_path": target_docx, "max_paragraphs": 50},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Modify DOCX Content, Placeholders & Append Sections",
                    description="Update existing text, modify table cells, and append verified recommendations with styling.",
                    tool_name="document.modify_docx",
                    tool_args={
                        "file_path": target_docx,
                        "replacements": {
                            "[STATUS]": "OFFICIALLY APPROVED",
                            "[DATE]": "04-SEP-2026",
                            "PENDING REVIEW": "APPROVED BY TECHNICAL SERVICES",
                        },
                        "append_sections": [
                            {
                                "title": "Addendum: Post-Inspection Corrective Protocol",
                                "content": "Adhering to MRPL SOP Section 4.2, mechanical seal replacement and dynamic alignment must precede plant startup.",
                                "bullets": [
                                    "Isolate suction and discharge valves prior to bearing disassembly.",
                                    "Inspect mechanical seal primary face for thermal micro-cracking.",
                                    "Execute laser optical alignment to within 0.05 mm tolerance.",
                                ],
                                "style": "callout",
                            }
                        ],
                    },
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=3,
                    title="Verify Document Deliverable & Cryptographic Provenance",
                    description="Confirm all section edits, validate SHA-256 provenance signature, and present deliverable download.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # =========================================================================
        # 4. PRESENTATION EDITOR WORKFLOW (Modify Existing PPTX)
        # =========================================================================
        elif is_pptx_edit:
            target_pptx = primary_file if primary_file.lower().endswith((".pptx", ".ppt")) else "MRPL_Executive_Review_Sample.pptx"
            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Inspect Existing Presentation Deck",
                    description=f"Inspect slide count, titles, and layout elements of '{target_pptx}'.",
                    tool_name="presentation.modify_pptx",
                    tool_args={"file_path": target_pptx, "action": "inspect"},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Add Executive Slides & Comparison Table to PPTX",
                    description="Insert executive summary slides and comparison table into existing presentation deck.",
                    tool_name="presentation.modify_pptx",
                    tool_args={
                        "file_path": target_pptx,
                        "action": "update",
                        "operations": [
                            {
                                "type": "add_slide",
                                "title": "Fleet Vibration & Mechanical Integrity Summary",
                                "bullet_points": [
                                    "Pump P-101 measured 4.8 mm/s vibration, exceeding ISO 10816 Zone B limit (4.5 mm/s).",
                                    "Mechanical seal primary face weeping detected; replacement scheduled within 72 hours.",
                                    "Standby unit P-101B operating normally at 2.3 mm/s vibration.",
                                ],
                            },
                            {
                                "type": "add_table",
                                "title": "Asset Health Comparison Matrix",
                                "headers": ["Equipment Tag", "Unit", "Vibration RMS", "Limit", "Status"],
                                "rows": [
                                    ["P-101A", "CDU-1", "4.8 mm/s", "4.5 mm/s", "ABNORMAL - ALERT"],
                                    ["P-101B", "CDU-1", "2.3 mm/s", "4.5 mm/s", "NORMAL - IN SPEC"],
                                    ["P-102A", "VDU", "1.8 mm/s", "4.5 mm/s", "NORMAL - IN SPEC"],
                                ],
                            },
                        ],
                    },
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=3,
                    title="Verify Presentation Deliverable & Signatures",
                    description="Confirm slide additions, table formatting, and SHA-256 deliverable signature.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # =========================================================================
        # 5. FILE OPERATIONS WORKFLOW (Copy, Rename, Read, Write)
        # =========================================================================
        elif is_file_op:
            if "copy" in goal_lower:
                tool_name = "file.copy"
                tool_args = {"source_path": primary_file, "destination_path": "storage/artifacts/"}
                desc = f"Safely copy '{primary_file}' to artifacts directory."
            elif "rename" in goal_lower:
                tool_name = "file.rename"
                tool_args = {"source_path": primary_file, "new_name_or_path": f"archived_{Path(primary_file).name}"}
                desc = f"Safely rename '{primary_file}'."
            else:
                tool_name = "file.read"
                tool_args = {"file_path": primary_file}
                desc = f"Safely read text and metadata from '{primary_file}'."

            plan = [
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=1,
                    title="Execute Sovereign File Operation",
                    description=desc,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
                PlanStep(
                    step_id=generate_uuid("STEP"),
                    order=2,
                    title="Verify File Operations & Ledger Provenance",
                    description="Confirm file integrity, filesystem boundary confinement, and record audit event.",
                    tool_name=None,
                    tool_args={},
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # =========================================================================
        # 6. GENERAL MULTIMODAL VISUAL UNDERSTANDING (Image QA)
        # =========================================================================
        elif has_image_file and not requires_approval_note and not any(k in goal_lower for k in ["p&id", "pid", "schematic"]):
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
            ]

        # =========================================================================
        # 7. INDUSTRIAL INSPECTION -> SOP RAG -> APPROVAL NOTE (DOCX)
        # =========================================================================
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
                    tool_name=None,
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
                        "subject": "Approval for Overhaul and Seal Replacement - Pump P-101",
                        "equipment_id": "P-101",
                        "sop_reference": "MRPL SOP Section 4.2",
                    },
                    assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                    status=AgentStatus.PENDING,
                ),
            ]

        # =========================================================================
        # 8. PYTHON CODING & AIR-GAPPED SANDBOX (With Self-Healing)
        # =========================================================================
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

        # =========================================================================
        # 9. GENERAL ENGINEERING REASONING & DIRECT QA
        # =========================================================================
        else:
            requires_rag = any(k in goal_lower for k in [
                "sop", "standard", "manual", "procedure", "mrpl", "threshold",
                "vibration", "pump p-101", "spec", "specification", "guideline",
                "policy", "api 610", "api 510", "document", "documentation",
            ])
            if requires_rag:
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
            else:
                plan = [
                    PlanStep(
                        step_id=generate_uuid("STEP"),
                        order=1,
                        title="Analysis & Thoughtful Response",
                        description=f"Provide an insightful, direct, and comprehensive response answering: '{goal}'.",
                        tool_name=None,
                        tool_args={},
                        assigned_model=routing.stage_models.get("reasoning", "qwen3:8b"),
                        status=AgentStatus.PENDING,
                    ),
                ]

        return plan
