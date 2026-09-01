import ast
import math
import operator
from typing import Any, Dict, List, Optional
from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission


class SafeMathEvaluator(ast.NodeVisitor):
    """Safely evaluates mathematical expressions using AST parsing without calling eval()."""

    # Supported binary operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.BitXor: operator.pow,  # Support ^ as power notation (common in engineering)
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Supported math functions and constants
    FUNCTIONS = {
        "sqrt": math.sqrt,
        "log": math.log,
        "log10": math.log10,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "radians": math.radians,
        "degrees": math.degrees,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "ceil": math.ceil,
        "floor": math.floor,
        "min": min,
        "max": max,
        "pow": pow,
    }

    CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "g": 9.81,           # Acceleration due to gravity (m/s^2)
        "rho_water": 1000.0, # Water density (kg/m^3)
    }

    def evaluate(self, expression_str: str) -> float:
        """Parse and evaluate expression."""
        clean_expr = expression_str.strip().replace("^", "**")
        try:
            node = ast.parse(clean_expr, mode="eval")
            return self.visit(node.body)
        except ZeroDivisionError:
            raise ValueError("Division by zero in mathematical expression.")
        except Exception as e:
            raise ValueError(f"Invalid math expression '{expression_str}': {str(e)}")

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Num(self, node: ast.Num) -> Any:  # for Python < 3.8 compat
        return node.n

    def visit_Name(self, node: ast.Name) -> Any:
        name_lower = node.id.lower()
        if name_lower in self.CONSTANTS:
            return self.CONSTANTS[name_lower]
        raise ValueError(f"Unknown variable or constant: '{node.id}'")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op_type = type(node.op)
        if op_type in self.OPERATORS:
            operand = self.visit(node.operand)
            return self.OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op_type = type(node.op)
        if op_type in self.OPERATORS:
            left = self.visit(node.left)
            right = self.visit(node.right)
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero.")
            return self.OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are supported.")
        func_name = node.func.id.lower()
        if func_name not in self.FUNCTIONS:
            raise ValueError(f"Unsupported math function: '{func_name}'")
        args = [self.visit(arg) for arg in node.args]
        return self.FUNCTIONS[func_name](*args)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Disallowed syntax node: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Deterministic engineering calculation tool using safe AST mathematical evaluation."""

    def __init__(self):
        self._evaluator = SafeMathEvaluator()

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Safely evaluate precision mathematical and hydraulic formulas (e.g. '150 * 45 * 850 * 9.81 / 3.6e6', "
            "'sqrt(2 * g * 12.5)', 'pi * (0.15 / 2)**2')."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical formula to compute (supports + - * / ^ sqrt, log, sin, cos, pi, g)",
                }
            },
            "required": ["expression"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
                "result": {"type": "number"},
                "formatted": {"type": "string"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.CALCULATOR]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        expression = arguments.get("expression", "")
        if not expression or not isinstance(expression, str):
            return ToolResult(tool_name=self.name, success=False, error="Argument 'expression' must be a non-empty string.")

        try:
            val = self._evaluator.evaluate(expression)
            # Format nicely
            if isinstance(val, float) and val.is_integer():
                formatted = str(int(val))
            elif isinstance(val, float):
                formatted = f"{val:.6g}"
            else:
                formatted = str(val)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output={
                    "expression": expression,
                    "result": val,
                    "formatted": formatted,
                },
                metadata={"computed_value": val},
            )
        except ZeroDivisionError:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="Division by zero in mathematical expression.",
                metadata={"expression": expression},
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                metadata={"expression": expression},
            )
