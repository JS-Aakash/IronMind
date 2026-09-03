import ast
import re
from typing import List, Optional, Tuple


class SandboxSecurityViolation(Exception):
    """Raised when generated code violates air-gap and isolation security policies."""
    pass


class CodeSecurityScanner:
    """Static AST and lexical scanner to detect malicious or forbidden host operations in generated Python code."""

    FORBIDDEN_MODULES = {
        "subprocess",
        "pty",
        "multiprocessing",
        "posix",
        "ctypes",
    }

    FORBIDDEN_ATTRIBUTES = {
        "system",
        "popen",
        "spawn",
        "execv",
        "fork",
        "kill",
        "rmdir",
    }

    HOST_FILESYSTEM_PATTERNS = [
        r"(/etc/passwd|/etc/shadow|/etc/hosts|/etc/sudoers)",
        r"([A-Za-z]:\\(?:Windows\\System32|System32)|/root/\.ssh|/home/[^/]+/\.ssh)",
        r"(\.\./|\.\.\\)",  # Path traversal
        r"(\.env|credentials\.json)",
    ]

    NETWORK_CALL_PATTERNS = [
        r"(socket\.socket|socket\.connect)",
        r"(urllib\.request|urllib3|requests\.get|requests\.post|aiohttp|httpx)",
        r"(http://|https://|ftp://)",
    ]

    def scan_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Scan code for security policy violations.

        Returns (is_safe, violation_reason).
        """
        # 1. Lexical checks for forbidden host paths
        for pattern in self.HOST_FILESYSTEM_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Prohibited host filesystem access pattern detected matching '{pattern}'."

        # 2. Lexical checks for network calls
        for pattern in self.NETWORK_CALL_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Prohibited outbound network access pattern detected matching '{pattern}'."

        # 3. AST Inspection
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Check string constants in AST
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val_lower = node.value.lower()
                    for pattern in self.HOST_FILESYSTEM_PATTERNS:
                        if re.search(pattern, val_lower, re.IGNORECASE):
                            return False, f"Prohibited host filesystem string detected: '{node.value}'."
                    for pattern in self.NETWORK_CALL_PATTERNS:
                        if re.search(pattern, val_lower, re.IGNORECASE):
                            return False, f"Prohibited network string detected: '{node.value}'."

                # Check imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        mod_root = alias.name.split(".")[0]
                        if mod_root in self.FORBIDDEN_MODULES:
                            return False, f"Prohibited module import: '{alias.name}' is blocked in Sovereign Sandbox."

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod_root = node.module.split(".")[0]
                        if mod_root in self.FORBIDDEN_MODULES:
                            return False, f"Prohibited module import: '{node.module}' is blocked in Sovereign Sandbox."

                # Check dangerous attribute accesses (e.g. os.system, os.popen)
                elif isinstance(node, ast.Attribute):
                    if node.attr in self.FORBIDDEN_ATTRIBUTES:
                        # Check if parent is os or similar
                        if isinstance(node.value, ast.Name) and node.value.id in ("os", "sys", "posix"):
                            return False, f"Prohibited system operation: '{node.value.id}.{node.attr}' is blocked in Sovereign Sandbox."

        except SyntaxError:
            # Let the Python sandbox compiler handle and report normal syntax errors explicitly
            pass
        except Exception as e:
            return False, f"Security scanning error: {str(e)}"

        return True, None
