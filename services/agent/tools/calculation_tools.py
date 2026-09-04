import ast
import logging
import math
import operator
import re
from typing import Any, Dict, List, Optional

from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.math_tools import SafeMathEvaluator
from services.agent.tools.security import ToolPermission

logger = logging.getLogger(__name__)


class StepByStepCalculationTool(BaseTool):
    """Deterministic engineering calculation engine providing auditable, step-by-step mathematical traces."""

    def __init__(self):
        self._evaluator = SafeMathEvaluator()

    @property
    def name(self) -> str:
        return "calculation.step_by_step"

    @property
    def description(self) -> str:
        return (
            "Evaluate precision engineering calculations and formulas step-by-step with complete mathematical "
            "provenance: Formula Definition → Variable Binding → Numerical Substitution → Intermediate Reductions → Final Result."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "formula": {
                    "type": "string",
                    "description": "Mathematical formula expression (e.g. '(Q * H * rho * g) / 3.6e6' or 'sqrt(2 * g * H)' or 'P_hyd / P_motor')",
                },
                "inputs": {
                    "type": "object",
                    "description": "Dictionary of named input variables and numeric values (e.g. {'Q': 150.0, 'H': 45.0, 'rho': 850.0, 'g': 9.81})",
                },
                "units": {
                    "type": "object",
                    "description": "Optional units map for inputs and result (e.g. {'Q': 'm^3/h', 'H': 'm', 'rho': 'kg/m^3', 'result': 'kW'})",
                },
                "description": {
                    "type": "string",
                    "description": "Engineering context or standard (e.g. 'Hydraulic Power Calculation adhering to API 610 Section 6.3')",
                },
            },
            "required": ["formula", "inputs"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "formula": {"type": "string"},
                "inputs": {"type": "object"},
                "substituted_expression": {"type": "string"},
                "step_by_step_trace": {"type": "array", "items": {"type": "string"}},
                "result": {"type": "number"},
                "formatted_result": {"type": "string"},
                "verified": {"type": "boolean"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.CALCULATOR]

    def _substitute_variables(self, formula: str, inputs: Dict[str, Any]) -> str:
        """Substitute variable names in formula string with formatted numerical values."""
        substituted = formula
        # Sort keys by length descending to prevent sub-string collision (e.g. P_hyd before P)
        sorted_keys = sorted(inputs.keys(), key=lambda k: len(k), reverse=True)
        for key in sorted_keys:
            val = inputs[key]
            # Replace variable identifier bounded by word boundaries
            pattern = rf"\b{re.escape(key)}\b"
            substituted = re.sub(pattern, str(val), substituted)
        return substituted

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        formula_str = arguments.get("formula", "").strip()
        inputs = arguments.get("inputs") or arguments.get("bindings") or {}
        units = arguments.get("units", {})
        if isinstance(units, str):
            units = {"result": units}
        if "unit" in arguments and isinstance(arguments["unit"], str):
            units["result"] = arguments["unit"]
        description = arguments.get("description", "Engineering Calculation")
        precision = int(arguments.get("precision", 4))

        if not formula_str:
            return ToolResult(tool_name=self.name, success=False, error="Argument 'formula' is required.")
        if not isinstance(inputs, dict):
            return ToolResult(tool_name=self.name, success=False, error="Argument 'inputs' or 'bindings' must be a dictionary.")

        # Clean formula
        clean_formula = formula_str.replace("^", "**")

        # Step 1: Formula definition
        trace: List[str] = [
            f"Step 1 [Formula Definition]: {description} governed by: {formula_str}"
        ]

        # Step 2: Variable binding
        bindings = []
        for k, v in inputs.items():
            unit_str = f" {units.get(k, '')}" if k in units else ""
            bindings.append(f"{k} = {v}{unit_str}")
        trace.append(f"Step 2 [Parameter Binding]: Given parameters: {', '.join(bindings)}")

        # Step 3: Numerical substitution
        substituted_expr = self._substitute_variables(clean_formula, inputs)
        trace.append(f"Step 3 [Numerical Substitution]: Expression becomes: {substituted_expr}")

        # Step 4: Step-by-step intermediate evaluation
        reduction_summary = substituted_expr
        try:
            # Check if fraction / division present
            if "/" in substituted_expr:
                parts = substituted_expr.split("/")
                if len(parts) == 2:
                    try:
                        num_val = self._evaluator.evaluate(parts[0].strip())
                        den_val = self._evaluator.evaluate(parts[1].strip())
                        reduction_summary = f"Numerator = {num_val:,.4f}, Denominator = {den_val:,.4f}"
                        trace.append(
                            f"Step 4 [Sub-Expression Reduction]: {reduction_summary}"
                        )
                    except Exception:
                        pass

            # Full evaluation
            final_result = self._evaluator.evaluate(substituted_expr)

            # Step 5: Final verified result
            result_unit = units.get("result", "")
            unit_suffix = f" {result_unit}" if result_unit else ""
            formatted_res = f"{final_result:,.4f}{unit_suffix}"
            trace.append(f"Step 5 [Final Verification]: Result = {formatted_res}")

            calc_trace_dict = {
                "step_1_formula": formula_str,
                "step_2_bindings": inputs,
                "step_3_substituted": substituted_expr,
                "step_4_reduction": reduction_summary,
                "step_5_verified_result": round(final_result, precision),
                "unit": result_unit,
                "notes": description,
            }

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "description": description,
                    "formula": formula_str,
                    "inputs": inputs,
                    "substituted_expression": substituted_expr,
                    "step_by_step_trace": trace,
                    "calculation_trace": calc_trace_dict,
                    "result": round(final_result, precision),
                    "formatted_result": formatted_res,
                    "verified": True,
                },
                metadata={
                    "formula": formula_str,
                    "result": round(final_result, precision),
                    "formatted": formatted_res,
                    "steps_count": len(trace),
                },
            )

        except ZeroDivisionError:
            return ToolResult(tool_name=self.name, success=False, error="Calculation error: Division by zero.")
        except Exception as e:
            logger.exception("Calculation engine error evaluating '%s': %s", substituted_expr, e)
            return ToolResult(tool_name=self.name, success=False, error=f"Calculation engine error: {str(e)}")
