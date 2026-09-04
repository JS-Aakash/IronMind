import os
import shutil
import pytest
import openpyxl
from docx import Document
from pptx import Presentation

from packages.shared.models.enums import TaskType
from services.agent.tools.registry import ToolRegistry
from services.agent.tools.spreadsheet_tools import SpreadsheetInspectTool, SpreadsheetModifyTool
from services.agent.tools.calculation_tools import StepByStepCalculationTool
from services.agent.tools.doc_tools import DocumentReadDocxTool, DocumentModifyDocxTool
from services.agent.tools.presentation_tools import PresentationModifyPptxTool
from services.agent.tools.file_tools import FileCopyTool, FileRenameTool
from services.agent.verifier import AgentVerifier
from services.agent.state import AgentState, ToolCallRecord


@pytest.fixture
def temp_test_dir():
    d = os.path.join("storage", "temp", "unit_tests")
    os.makedirs(d, exist_ok=True)
    yield d
    try:
        shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def sample_xlsx(temp_test_dir):
    file_path = os.path.join(temp_test_dir, "test_equipment.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vibration_Readings"
    ws.append(["Asset_Tag", "Subsystem", "Vibration_RMS_mms", "Operating_Hours", "Status"])
    ws.append(["P-101A", "Primary Impeller", 2.1, 4200, "NORMAL"])
    ws.append(["P-101B", "Secondary Impeller", 5.8, 4800, "ALERT"])
    ws.append(["P-102A", "Motor Drive End", 1.8, 3100, "NORMAL"])
    ws.append(["P-102B", "Motor Non-Drive End", 6.2, 5100, "CRITICAL"])
    wb.save(file_path)
    return file_path


@pytest.fixture
def sample_docx(temp_test_dir):
    file_path = os.path.join(temp_test_dir, "test_note.docx")
    doc = Document()
    doc.add_heading("EQUIPMENT INSPECTION REPORT", 0)
    p = doc.add_paragraph("Asset identifier: {{ASSET_TAG}}")
    p.add_run("\nStatus: {{STATUS}}")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Parameter"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Vibration"
    table.cell(1, 1).text = "0.0 mm/s"
    doc.save(file_path)
    return file_path


@pytest.fixture
def sample_pptx(temp_test_dir):
    file_path = os.path.join(temp_test_dir, "test_deck.pptx")
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Initial Equipment Review"
    prs.save(file_path)
    return file_path


class TestSpreadsheetAgent:
    @pytest.mark.asyncio
    async def test_inspect_spreadsheet(self, sample_xlsx):
        tool = SpreadsheetInspectTool()
        res = await tool.execute({"file_path": sample_xlsx})
        assert res.success is True
        assert res.output["total_sheets"] >= 1
        assert "Vibration_Readings" in res.output["sheets"]
        sheet_info = res.output["sheets"]["Vibration_Readings"]
        assert "Asset_Tag" in sheet_info["columns"]
        assert sheet_info["total_rows"] == 4

    @pytest.mark.asyncio
    async def test_modify_spreadsheet_and_create_summary(self, sample_xlsx):
        tool = SpreadsheetModifyTool()
        res = await tool.execute({
            "file_path": sample_xlsx,
            "action": "update",
            "sheet_name": "Vibration_Readings",
            "flag_abnormal": True,
            "abnormal_column": "Vibration_RMS_mms",
            "abnormal_threshold": 4.5,
            "create_summary_sheet": True,
            "summary_title": "KPI Summary",
        })
        assert res.success is True
        assert "updated_file" in res.output
        assert res.output["abnormal_assets_flagged"] == 2
        assert "sha256_hash" in res.output
        assert len(res.output["sha256_hash"]) == 64

        # Verify openpyxl output directly
        wb = openpyxl.load_workbook(res.output["updated_file"])
        assert "KPI Summary" in wb.sheetnames
        ws_summary = wb["KPI Summary"]
        assert "KPI SUMMARY" in ws_summary.cell(row=1, column=1).value

class TestCalculationEngine:
    @pytest.mark.asyncio
    async def test_step_by_step_calculation(self):
        tool = StepByStepCalculationTool()
        res = await tool.execute({
            "formula": "(Q * H * rho * g) / (P * 3600) * 100",
            "bindings": {
                "Q": 120.0,
                "H": 45.0,
                "rho": 1000.0,
                "g": 9.81,
                "P": 22.0,
            },
            "unit": "%",
            "precision": 2,
        })
        assert res.success is True
        trace = res.output["calculation_trace"]
        assert trace["step_1_formula"] == "(Q * H * rho * g) / (P * 3600) * 100"
        assert trace["step_5_verified_result"] == 66886.36
        assert trace["unit"] == "%"


class TestDocumentEditor:
    @pytest.mark.asyncio
    async def test_read_and_modify_docx(self, sample_docx):
        read_tool = DocumentReadDocxTool()
        read_res = await read_tool.execute({"file_path": sample_docx})
        assert read_res.success is True
        assert read_res.output["total_paragraphs"] >= 2

        modify_tool = DocumentModifyDocxTool()
        mod_res = await modify_tool.execute({
            "file_path": sample_docx,
            "replacements": {
                "{{ASSET_TAG}}": "P-101B",
                "{{STATUS}}": "VERIFIED OVERHAUL REQUIRED",
            },
            "add_sections": [
                {
                    "heading": "Diagnostic Telemetry",
                    "text": "Peak vibration exceeded ISO 10816 threshold (6.2 mm/s). Immediate bearing sleeve replacement recommended.",
                    "style": "Normal",
                }
            ],
        })
        assert mod_res.success is True
        assert mod_res.output["placeholders_replaced"] == 2
        assert "sha256_hash" in mod_res.output

        # Verify docx directly
        doc = Document(mod_res.output["updated_file"])
        full_text = "\n".join([p.text for p in doc.paragraphs])
        assert "P-101B" in full_text
        assert "VERIFIED OVERHAUL REQUIRED" in full_text
        assert "Diagnostic Telemetry" in full_text


class TestPresentationEditor:
    @pytest.mark.asyncio
    async def test_modify_pptx(self, sample_pptx):
        tool = PresentationModifyPptxTool()
        res = await tool.execute({
            "file_path": sample_pptx,
            "action": "update",
            "operations": [
                {
                    "type": "add_slide",
                    "title": "Abnormal Assets Diagnostic",
                    "bullet_points": [
                        "Pump P-101B vibration reached 5.8 mm/s.",
                        "Motor P-102B vibration reached 6.2 mm/s (Critical).",
                    ],
                },
                {
                    "type": "add_table",
                    "title": "Abnormal Asset Telemetry",
                    "headers": ["Asset Tag", "Vibration", "Status"],
                    "rows": [
                        ["P-101B", "5.8 mm/s", "Alert"],
                        ["P-102B", "6.2 mm/s", "Critical"],
                    ],
                },
            ],
        })
        assert res.success is True
        assert res.output["slide_count"] >= 2
        assert "sha256_hash" in res.output


class TestFileOperations:
    @pytest.mark.asyncio
    async def test_file_copy_and_rename(self, sample_xlsx, temp_test_dir):
        copy_tool = FileCopyTool()
        dst_copy = os.path.join(temp_test_dir, "test_equipment_backup.xlsx")
        c_res = await copy_tool.execute({"source_path": sample_xlsx, "destination_path": dst_copy})
        assert c_res.success is True
        assert os.path.exists(dst_copy)
        assert "sha256_hash" in c_res.output

        rename_tool = FileRenameTool()
        dst_renamed = os.path.join(temp_test_dir, "test_equipment_archived.xlsx")
        r_res = await rename_tool.execute({"source_path": dst_copy, "new_path": dst_renamed})
        assert r_res.success is True
        assert not os.path.exists(dst_copy)
        assert os.path.exists(dst_renamed)


class TestSovereignRegistryAndVerifier:
    def test_registry_contains_all_upgraded_tools(self):
        reg = ToolRegistry()
        tools = reg.get_all_tools()
        names = [t.name for t in tools]
        assert "spreadsheet.inspect" in names
        assert "spreadsheet.modify" in names
        assert "calculation.step_by_step" in names
        assert "document.read_docx" in names
        assert "document.modify_docx" in names
        assert "presentation.modify_pptx" in names
        assert "file.copy" in names
        assert "file.rename" in names
        assert "file.read" in names
        assert "file.write" in names

    def test_verifier_checks_spreadsheet_and_change_summary(self):
        verifier = AgentVerifier()
        state = AgentState(
            task_id="TASK_TEST_001",
            user_goal="Analyze equipment spreadsheet and flag abnormal assets",
            task_type=TaskType.GENERAL_REASONING,
            tool_calls=[
                ToolCallRecord(
                    call_id="call_1",
                    tool_name="spreadsheet.modify",
                    arguments={"flag_abnormal": True},
                    output={
                        "updated_file": "test.xlsx",
                        "abnormal_assets_flagged": 2,
                        "sha256_hash": "a" * 64,
                    },
                    success=True,
                ),
                ToolCallRecord(
                    call_id="call_2",
                    tool_name="calculation.step_by_step",
                    arguments={},
                    output={
                        "calculation_trace": {"step_5_verified_result": 74.2},
                    },
                    success=True,
                ),
            ],
            change_summaries=[
                {
                    "filename": "test.xlsx",
                    "action": "modified",
                    "changes": ["Flagged 2 abnormal assets", "Added KPI Summary sheet"],
                    "sha256_hash": "a" * 64,
                }
            ],
        )
        res = verifier.verify_execution(
            task_type=state.task_type.value,
            observations=["Analyzed spreadsheet and verified KPIs."],
            tool_results=[t.dict() for t in state.tool_calls],
            generated_artifacts=[{"filename": "test.xlsx", "sha256_hash": "a" * 64}],
            change_summaries=state.change_summaries,
        )
        assert res.passed is True
        findings_text = " ".join(res.findings)
        assert "Spreadsheet modifications" in findings_text
        assert "Step-by-step calculation trace verified" in findings_text
        assert "Recorded 1 verified file modification" in findings_text
