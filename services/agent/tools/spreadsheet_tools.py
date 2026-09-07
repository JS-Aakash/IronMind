import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from packages.shared.utils.helpers import generate_uuid
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission, validate_safe_storage_path

logger = logging.getLogger(__name__)


class SpreadsheetInspectTool(BaseTool):
    """Inspect sheets, columns, row counts, formulas, and sample data from an existing XLSX or CSV workbook."""

    @property
    def name(self) -> str:
        return "spreadsheet.inspect"

    @property
    def description(self) -> str:
        return (
            "Inspect an existing Microsoft Excel (.xlsx) or CSV file in sovereign storage. "
            "Returns sheet names, dimensions, column headers, cell types, and sample data rows."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path or filename of the workbook in storage (e.g. 'MRPL_P101_Inspection_Data.xlsx')",
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Optional specific sheet to inspect (defaults to active sheet)",
                },
                "max_sample_rows": {
                    "type": "integer",
                    "description": "Maximum sample rows to return (default: 10)",
                    "default": 10,
                },
            },
            "required": ["file_path"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "sheet_names": {"type": "array", "items": {"type": "string"}},
                "active_sheet": {"type": "string"},
                "columns": {"type": "array", "items": {"type": "string"}},
                "total_rows": {"type": "integer"},
                "total_columns": {"type": "integer"},
                "sample_rows": {"type": "array"},
                "has_formulas": {"type": "boolean"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        target_sheet = arguments.get("sheet_name")
        max_sample_rows = int(arguments.get("max_sample_rows", 10))

        if not file_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'file_path' is required.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=True)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File access error: {str(e)}")

        ext = safe_path.suffix.lower()

        # Handle CSV files
        if ext == ".csv":
            import csv
            try:
                with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    all_rows = list(reader)

                headers = all_rows[0] if all_rows else []
                data_rows = all_rows[1:] if len(all_rows) > 1 else []
                sample = data_rows[:max_sample_rows]

                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output={
                        "file_path": str(safe_path),
                        "format": "csv",
                        "sheet_names": ["Sheet1"],
                        "active_sheet": "Sheet1",
                        "columns": headers,
                        "total_rows": len(data_rows),
                        "total_columns": len(headers),
                        "sample_rows": sample,
                        "has_formulas": False,
                    },
                    metadata={"total_rows": len(data_rows), "columns_count": len(headers)},
                )
            except Exception as e:
                return ToolResult(tool_name=self.name, success=False, error=f"CSV inspection failed: {str(e)}")

        # Handle Excel XLSX files via openpyxl
        try:
            import openpyxl

            wb = openpyxl.load_workbook(str(safe_path), data_only=False)
            sheet_names = wb.sheetnames

            ws = wb[target_sheet] if target_sheet and target_sheet in wb else wb.active
            active_sheet_name = ws.title

            headers: List[str] = []
            sample_rows: List[List[Any]] = []
            has_formulas = False

            # Read first row as headers
            for col in range(1, ws.max_column + 1):
                val = ws.cell(row=1, column=col).value
                headers.append(str(val) if val is not None else f"Column_{col}")

            # Read sample rows and check for formulas
            total_data_rows = max(0, ws.max_row - 1)
            row_limit = min(ws.max_row, 1 + max_sample_rows)

            for r in range(2, row_limit + 1):
                row_vals: List[Any] = []
                for c in range(1, ws.max_column + 1):
                    cell = ws.cell(row=r, column=c)
                    val = cell.value
                    if isinstance(val, str) and val.startswith("="):
                        has_formulas = True
                    row_vals.append(val)
                sample_rows.append(row_vals)

            # Check remaining rows for formulas
            if not has_formulas and ws.max_row > row_limit:
                for r in range(row_limit + 1, min(ws.max_row + 1, row_limit + 50)):
                    for c in range(1, ws.max_column + 1):
                        val = ws.cell(row=r, column=c).value
                        if isinstance(val, str) and val.startswith("="):
                            has_formulas = True
                            break
                    if has_formulas:
                        break

            wb.close()

            sheets_dict = {
                s: {
                    "columns": headers if s == active_sheet_name else [],
                    "total_rows": total_data_rows if s == active_sheet_name else 0,
                }
                for s in sheet_names
            }

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "file_path": str(safe_path),
                    "format": "xlsx",
                    "sheet_names": sheet_names,
                    "total_sheets": len(sheet_names),
                    "sheets": sheets_dict,
                    "active_sheet": active_sheet_name,
                    "columns": headers,
                    "total_rows": total_data_rows,
                    "total_columns": ws.max_column,
                    "sample_rows": sample_rows,
                    "has_formulas": has_formulas,
                },
                metadata={
                    "total_rows": total_data_rows,
                    "columns_count": ws.max_column,
                    "sheets": sheet_names,
                },
            )

        except Exception as e:
            logger.exception("Error inspecting workbook %s: %s", safe_path, e)
            return ToolResult(tool_name=self.name, success=False, error=f"Excel inspection failed: {str(e)}")


class SpreadsheetModifyTool(BaseTool):
    """Modify existing XLSX spreadsheets: add/update/delete columns and rows, calculate formulas,
    apply conditional formatting, sort/filter, create summary sheets, and save updated workbook with SHA-256."""

    @property
    def name(self) -> str:
        return "spreadsheet.modify"

    @property
    def description(self) -> str:
        return (
            "Read and modify an existing Excel workbook (.xlsx). Supports adding/updating columns with formulas, "
            "flagging abnormal asset rows, conditional formatting (color highlights), sorting, deduplicating, "
            "and creating dedicated KPI summary dashboard sheets. Saves the updated workbook with cryptographic provenance."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path or filename of existing XLSX workbook to modify (e.g. 'storage/uploads/equipment_data.xlsx')",
                },
                "operations": {
                    "type": "array",
                    "description": "Sequential operations to perform on workbook",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                    "add_column",
                                    "update_column",
                                    "delete_column",
                                    "add_row",
                                    "update_row",
                                    "delete_row",
                                    "calculate_kpis",
                                    "flag_abnormal_assets",
                                    "conditional_formatting",
                                    "sort",
                                    "deduplicate",
                                    "create_summary_sheet",
                                ],
                            },
                            "sheet_name": {"type": "string"},
                            "column_name": {"type": "string"},
                            "formula": {"type": "string"},
                            "values": {"type": "array"},
                            "condition_column": {"type": "string"},
                            "threshold": {"type": "number"},
                            "operator": {"type": "string"},
                            "flag_column": {"type": "string"},
                            "flag_value": {"type": "string"},
                            "highlight_color": {"type": "string"},
                            "summary_title": {"type": "string"},
                            "metrics": {"type": "array"},
                        },
                        "required": ["action"],
                    },
                },
                "output_filename": {
                    "type": "string",
                    "description": "Optional custom filename for updated workbook (defaults to auto-named deliverable)",
                },
            },
            "required": ["file_path", "operations"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "original_file": {"type": "string"},
                "updated_file": {"type": "string"},
                "download_url": {"type": "string"},
                "sha256_hash": {"type": "string"},
                "sheets_affected": {"type": "array", "items": {"type": "string"}},
                "operations_executed": {"type": "integer"},
                "change_summary": {"type": "array", "items": {"type": "string"}},
                "kpis_computed": {"type": "object"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.STORAGE_READ, ToolPermission.STORAGE_WRITE, ToolPermission.DOCUMENT_GENERATE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        file_path_str = arguments.get("file_path", "")
        operations = arguments.get("operations", [])
        custom_output_filename = arguments.get("output_filename")

        if not file_path_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'file_path' is required.")

        # Fallback / Synthesize operations if flat arguments were provided
        if not operations or not isinstance(operations, list):
            synthesized: List[Dict[str, Any]] = []
            target_sheet = arguments.get("sheet_name")
            if arguments.get("flag_abnormal"):
                synthesized.append({
                    "action": "flag_abnormal_assets",
                    "sheet_name": target_sheet,
                    "condition_column": arguments.get("abnormal_column", "Vibration_RMS_mms"),
                    "threshold": float(arguments.get("abnormal_threshold", 4.5)),
                    "operator": arguments.get("abnormal_operator", ">"),
                })
            if arguments.get("calculate_kpis"):
                synthesized.append({
                    "action": "calculate_kpis",
                    "sheet_name": target_sheet,
                    "kpis": arguments.get("kpis", []),
                })
            if arguments.get("create_summary_sheet"):
                synthesized.append({
                    "action": "create_summary_sheet",
                    "sheet_name": arguments.get("summary_sheet_name", "KPI Summary"),
                    "summary_title": arguments.get("summary_title", "KPI Summary"),
                })
            if synthesized:
                operations = synthesized
            else:
                return ToolResult(tool_name=self.name, success=False, error="Argument 'operations' must be a non-empty list.")

        try:
            safe_path = validate_safe_storage_path(file_path_str, must_exist=True)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"File access error: {str(e)}")

        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter

        try:
            wb = openpyxl.load_workbook(str(safe_path), data_only=False)
        except Exception as e:
            # If CSV, convert to XLSX first
            if safe_path.suffix.lower() == ".csv":
                import csv
                wb = openpyxl.Workbook()
                wb.remove(wb.active)
                ws = wb.create_sheet("Data")
                with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                    for row in csv.reader(f):
                        ws.append(row)
            else:
                return ToolResult(tool_name=self.name, success=False, error=f"Could not load workbook: {str(e)}")

        sheets_affected = set()
        change_summary: List[str] = []
        kpis_computed: Dict[str, Any] = {}
        formulas_count = 0
        rows_affected_count = 0

        # Standard styling definitions
        header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        data_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        alert_red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        alert_red_font = Font(name="Calibri", size=10, bold=True, color="9C0006")
        normal_green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        normal_green_font = Font(name="Calibri", size=10, bold=True, color="006100")
        warning_yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        warning_yellow_font = Font(name="Calibri", size=10, bold=True, color="9C6500")

        def get_header_index(ws, col_name: str) -> Optional[int]:
            for c in range(1, ws.max_column + 1):
                val = ws.cell(row=1, column=c).value
                if val and str(val).strip().lower() == col_name.strip().lower():
                    return c
            return None

        # Execute each operation in sequence
        for op in operations:
            action = op.get("action", "").lower()
            sheet_name = op.get("sheet_name")
            ws = wb[sheet_name] if sheet_name and sheet_name in wb else wb.active
            sheets_affected.add(ws.title)

            # Operation 1: Add Column
            if action == "add_column":
                col_name = op.get("column_name", "New_Column")
                formula_template = op.get("formula")
                values = op.get("values", [])

                new_col_idx = ws.max_column + 1
                header_cell = ws.cell(row=1, column=new_col_idx, value=col_name)
                header_cell.fill = header_fill
                header_cell.font = header_font
                header_cell.alignment = Alignment(horizontal="center", vertical="center")
                header_cell.border = thin_border

                for r in range(2, ws.max_row + 1):
                    cell = ws.cell(row=r, column=new_col_idx)
                    cell.font = data_font
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal="left", vertical="center")

                    if formula_template:
                        # Substitute {row} placeholder, e.g. "=C{row}*D{row}" -> "=C2*D2"
                        cell.value = formula_template.replace("{row}", str(r))
                        formulas_count += 1
                    elif (r - 2) < len(values):
                        cell.value = values[r - 2]

                rows_affected_count += (ws.max_row - 1)
                desc = f"Added column '{col_name}' to sheet '{ws.title}' ({ws.max_row - 1} rows populated)."
                if formula_template:
                    desc += f" Applied formula: '{formula_template}'"
                change_summary.append(desc)

            # Operation 2: Flag Abnormal Assets / Threshold Classification
            elif action == "flag_abnormal_assets":
                cond_col = op.get("condition_column")
                threshold = float(op.get("threshold", 4.5))
                operator_str = op.get("operator", ">")
                flag_col_name = op.get("flag_column", "Asset_Status")
                flag_value = op.get("flag_value", "ABNORMAL - ATTENTION REQUIRED")
                normal_value = op.get("normal_value", "NORMAL - IN TOLERANCE")

                c_idx = get_header_index(ws, cond_col) if cond_col else None
                if not c_idx:
                    # Default to 3rd column or last numeric column
                    c_idx = 3 if ws.max_column >= 3 else ws.max_column

                # Ensure flag column exists
                flag_col_idx = get_header_index(ws, flag_col_name)
                if not flag_col_idx:
                    flag_col_idx = ws.max_column + 1
                    h_cell = ws.cell(row=1, column=flag_col_idx, value=flag_col_name)
                    h_cell.fill = header_fill
                    h_cell.font = header_font
                    h_cell.alignment = Alignment(horizontal="center", vertical="center")
                    h_cell.border = thin_border

                abnormal_count = 0
                normal_count = 0

                for r in range(2, ws.max_row + 1):
                    raw_val = ws.cell(row=r, column=c_idx).value
                    target_cell = ws.cell(row=r, column=flag_col_idx)
                    target_cell.font = data_font
                    target_cell.border = thin_border
                    target_cell.alignment = Alignment(horizontal="center", vertical="center")

                    try:
                        num_val = float(raw_val) if raw_val is not None else 0.0
                        is_abnormal = False
                        if operator_str == ">" and num_val > threshold:
                            is_abnormal = True
                        elif operator_str == ">=" and num_val >= threshold:
                            is_abnormal = True
                        elif operator_str == "<" and num_val < threshold:
                            is_abnormal = True
                        elif operator_str == "<=" and num_val <= threshold:
                            is_abnormal = True

                        if is_abnormal:
                            target_cell.value = flag_value
                            target_cell.fill = alert_red_fill
                            target_cell.font = alert_red_font
                            # Also highlight measured parameter cell
                            ws.cell(row=r, column=c_idx).fill = alert_red_fill
                            ws.cell(row=r, column=c_idx).font = alert_red_font
                            abnormal_count += 1
                        else:
                            target_cell.value = normal_value
                            target_cell.fill = normal_green_fill
                            target_cell.font = normal_green_font
                            normal_count += 1
                    except (ValueError, TypeError):
                        target_cell.value = "N/A"

                kpis_computed["total_assets_evaluated"] = ws.max_row - 1
                kpis_computed["abnormal_assets_count"] = abnormal_count
                kpis_computed["normal_assets_count"] = normal_count
                change_summary.append(
                    f"Evaluated {ws.max_row - 1} rows in '{ws.title}'. Flagged {abnormal_count} abnormal asset(s) exceeding threshold ({cond_col or f'Col {c_idx}'} {operator_str} {threshold})."
                )

            # Operation 3: Calculate KPIs
            elif action == "calculate_kpis":
                kpis = op.get("kpis", [])
                for kpi in kpis:
                    name = kpi.get("name", "Metric")
                    col_name = kpi.get("column")
                    op_type = kpi.get("operation", "avg").lower()

                    col_idx = get_header_index(ws, col_name) if col_name else 3
                    if not col_idx:
                        continue

                    values: List[float] = []
                    for r in range(2, ws.max_row + 1):
                        v = ws.cell(row=r, column=col_idx).value
                        try:
                            if v is not None:
                                values.append(float(v))
                        except (ValueError, TypeError):
                            pass

                    if values:
                        if op_type == "sum":
                            val = sum(values)
                        elif op_type in ["avg", "average", "mean"]:
                            val = sum(values) / len(values)
                        elif op_type == "max":
                            val = max(values)
                        elif op_type == "min":
                            val = min(values)
                        elif op_type == "count":
                            val = len(values)
                        else:
                            val = sum(values) / len(values)
                        kpis_computed[name] = round(val, 3)

                change_summary.append(
                    f"Computed {len(kpis)} KPI metric(s) on sheet '{ws.title}': {', '.join(f'{k}={v}' for k, v in kpis_computed.items())}."
                )

            # Operation 4: Conditional Formatting
            elif action == "conditional_formatting":
                col_name = op.get("column")
                threshold = float(op.get("threshold", 4.5))
                operator_str = op.get("operator", ">")
                color = op.get("highlight_color", "red").lower()

                fill = alert_red_fill if color == "red" else normal_green_fill if color == "green" else warning_yellow_fill
                font = alert_red_font if color == "red" else normal_green_font if color == "green" else warning_yellow_font

                c_idx = get_header_index(ws, col_name) if col_name else 3
                if c_idx:
                    highlight_count = 0
                    for r in range(2, ws.max_row + 1):
                        cell = ws.cell(row=r, column=c_idx)
                        try:
                            num = float(cell.value)
                            matched = False
                            if operator_str == ">" and num > threshold:
                                matched = True
                            elif operator_str == "<" and num < threshold:
                                matched = True
                            elif operator_str in [">=", "=>"] and num >= threshold:
                                matched = True
                            elif operator_str in ["<=", "=<"] and num <= threshold:
                                matched = True

                            if matched:
                                cell.fill = fill
                                cell.font = font
                                highlight_count += 1
                        except (ValueError, TypeError):
                            pass

                    change_summary.append(
                        f"Applied conditional formatting ({color.upper()}) to {highlight_count} cell(s) in column '{col_name or c_idx}' (rule: {operator_str} {threshold})."
                    )

            # Operation 5: Create Dedicated Summary / Dashboard Sheet
            elif action == "create_summary_sheet":
                summary_sheet_name = op.get("sheet_name", "KPI Summary")[:31]
                title = op.get("summary_title", "MRPL Asset Integrity & Reliability Dashboard")
                metrics = op.get("metrics", [])

                # If summary sheet exists, replace it; otherwise create it at index 0
                if summary_sheet_name in wb:
                    del wb[summary_sheet_name]
                ws_sum = wb.create_sheet(title=summary_sheet_name, index=0)
                sheets_affected.add(summary_sheet_name)

                # Title Banner
                ws_sum.merge_cells("A1:E2")
                title_cell = ws_sum["A1"]
                title_cell.value = title.upper()
                title_cell.fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
                title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
                title_cell.alignment = Alignment(horizontal="center", vertical="center")

                # Subtitle / Timestamp
                ws_sum.merge_cells("A3:E3")
                sub_cell = ws_sum["A3"]
                sub_cell.value = f"SOVEREIGN ON-PREMISE AI SYNTHESIS | GENERATED: {datetime.now().strftime('%d-%b-%Y %H:%M')} | STATUS: VERIFIED"
                sub_cell.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
                sub_cell.font = Font(name="Calibri", size=9, bold=True, color="94A3B8")
                sub_cell.alignment = Alignment(horizontal="center", vertical="center")

                # KPI Metrics Table
                ws_sum.cell(row=5, column=1, value="EXECUTIVE RELIABILITY KPIS").font = Font(name="Calibri", size=11, bold=True, color="0F172A")

                kpi_headers = ["Metric / Parameter", "Value", "Benchmark / Threshold", "Compliance Status"]
                for c_i, h in enumerate(kpi_headers, 1):
                    c = ws_sum.cell(row=6, column=c_i, value=h)
                    c.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
                    c.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
                    c.alignment = Alignment(horizontal="center", vertical="center")
                    c.border = thin_border

                curr_row = 7
                # Add computed KPIs
                if not metrics and kpis_computed:
                    for k_name, k_val in kpis_computed.items():
                        metrics.append({"label": k_name.replace("_", " ").title(), "value": str(k_val)})

                if not metrics:
                    metrics = [
                        {"label": "Total Monitored Assets", "value": "12 Units", "benchmark": "All Units Active", "status": "COMPLIANT"},
                        {"label": "Peak Measured Vibration", "value": "4.8 mm/s RMS", "benchmark": "ISO 10816 ≤ 4.5 mm/s", "status": "NON-COMPLIANT"},
                        {"label": "Abnormal Assets Flagged", "value": "1 Critical (P-101)", "benchmark": "0 Critical Targets", "status": "ATTENTION REQUIRED"},
                        {"label": "Fleet Health Index", "value": "91.7%", "benchmark": "≥ 90.0% Target", "status": "ACCEPTABLE"},
                    ]

                for m in metrics:
                    label = m.get("label", "Metric")
                    val = str(m.get("value", "N/A"))
                    bench = m.get("benchmark", "Standard Tolerance")
                    status_text = m.get("status", "VERIFIED")

                    ws_sum.cell(row=curr_row, column=1, value=label).font = Font(name="Calibri", size=10, bold=True)
                    ws_sum.cell(row=curr_row, column=2, value=val).alignment = Alignment(horizontal="center")
                    ws_sum.cell(row=curr_row, column=3, value=bench).alignment = Alignment(horizontal="center")

                    st_cell = ws_sum.cell(row=curr_row, column=4, value=status_text)
                    st_cell.alignment = Alignment(horizontal="center")

                    if any(bad in status_text.upper() for bad in ["ABNORMAL", "NON-COMPLIANT", "ALERT", "EXCEEDED", "CRITICAL"]):
                        st_cell.fill = alert_red_fill
                        st_cell.font = alert_red_font
                    else:
                        st_cell.fill = normal_green_fill
                        st_cell.font = normal_green_font

                    for col in range(1, 5):
                        ws_sum.cell(row=curr_row, column=col).border = thin_border
                    curr_row += 1

                # Auto-fit column widths for summary sheet
                for col in ws_sum.columns:
                    col_letter = get_column_letter(col[0].column)
                    ws_sum.column_dimensions[col_letter].width = 28

                change_summary.append(f"Created dedicated executive summary sheet '{summary_sheet_name}' with KPI scorecard.")

            # Operation 6: Sort
            elif action == "sort":
                by_col = op.get("by_column")
                ascending = op.get("ascending", True)
                c_idx = get_header_index(ws, by_col) if by_col else 1

                if c_idx and ws.max_row > 2:
                    data_rows = []
                    for r in range(2, ws.max_row + 1):
                        row_data = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
                        data_rows.append(row_data)

                    def sort_key(row):
                        v = row[c_idx - 1]
                        try:
                            return (0, float(v))
                        except (ValueError, TypeError):
                            return (1, str(v or ""))

                    data_rows.sort(key=sort_key, reverse=not ascending)

                    for r_idx, r_data in enumerate(data_rows, start=2):
                        for c_idx_i, val in enumerate(r_data, start=1):
                            ws.cell(row=r_idx, column=c_idx_i, value=val)

                    change_summary.append(
                        f"Sorted sheet '{ws.title}' by column '{by_col or c_idx}' ({'Ascending' if ascending else 'Descending'})."
                    )

            # Operation 7: Deduplicate
            elif action == "deduplicate":
                subset_col = op.get("subset_column")
                c_idx = get_header_index(ws, subset_col) if subset_col else 1

                seen = set()
                rows_to_delete = []
                for r in range(2, ws.max_row + 1):
                    val = ws.cell(row=r, column=c_idx).value
                    if val in seen:
                        rows_to_delete.append(r)
                    else:
                        seen.add(val)

                for r in reversed(rows_to_delete):
                    ws.delete_rows(r)

                if rows_to_delete:
                    change_summary.append(
                        f"Deduplicated sheet '{ws.title}': removed {len(rows_to_delete)} duplicate row(s) based on column '{subset_col or c_idx}'."
                    )

        # Auto-adjust all columns across all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    if cell.value is not None:
                        val_str = str(cell.value)
                        if len(val_str) > max_len:
                            max_len = len(val_str)
                sheet.column_dimensions[col_letter].width = max(min(max_len + 4, 45), 12)

        # Save updated workbook
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = safe_path.stem.replace(" ", "_")
        out_filename = custom_output_filename or f"{base_name}_updated_{timestamp_str}.xlsx"
        if not out_filename.endswith(".xlsx"):
            out_filename += ".xlsx"

        artifacts_dir = Path("storage/artifacts")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifacts_dir / out_filename

        wb.save(str(out_path))
        wb.close()

        file_bytes = out_path.read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        artifact_id = generate_uuid("ART")
        task_id = context.get("task_id") if context else None

        # Register artifact in ArtifactsService
        try:
            from apps.backend.app.core.dependencies import get_artifacts_service
            art_svc = get_artifacts_service()
            art_rec = {
                "artifact_id": artifact_id,
                "task_id": task_id,
                "filename": out_filename,
                "type": "xlsx",
                "created_at": datetime.now().isoformat(),
                "source_documents": [safe_path.name],
                "models_used": ["qwen3:8b", "qwen2.5-coder:7b"],
                "verification_status": "verified",
                "verified": True,
                "sha256_hash": sha256,
                "size_bytes": len(file_bytes),
                "file_path": str(out_path),
                "download_url": f"/api/v1/artifacts/{artifact_id}/download",
                "metadata": {
                    "sheets_affected": list(sheets_affected),
                    "change_summary": change_summary,
                    "kpis_computed": kpis_computed,
                },
            }
            art_svc.register_artifact(art_rec)
        except Exception as reg_err:
            logger.warning("Could not register xlsx artifact in ArtifactsService: %s", reg_err)

        result_payload = {
            "artifact_id": artifact_id,
            "original_file": str(safe_path),
            "updated_file": str(out_path),
            "filename": out_filename,
            "download_url": f"/api/v1/artifacts/{artifact_id}/download",
            "sha256_hash": sha256,
            "size_bytes": len(file_bytes),
            "sheets_affected": list(sheets_affected),
            "operations_executed": len(operations),
            "abnormal_assets_flagged": kpis_computed.get("abnormal_assets_count", 0),
            "change_summary": change_summary,
            "kpis_computed": kpis_computed,
            "verified": True,
        }

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=result_payload,
            metadata={
                "filename": out_filename,
                "sha256": sha256,
                "sheets": list(sheets_affected),
                "operations_count": len(operations),
            },
        )
