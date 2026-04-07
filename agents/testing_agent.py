"""
Jarvis v6 - Testing Agent
===========================
Runs the generated project, captures output, and detects errors.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from agents.execution_agent import ExecutionAgent


class TestingAgent:
    """Test the generated project by running it and analysing output.

    Does NOT use the LLM. Uses ExecutionAgent.run_command() to execute.
    """

    def __init__(self, name: str = "TestingAgent", timeout: int = 30) -> None:
        self.name = name
        self.timeout = timeout
        self.executor = ExecutionAgent()
        self._error_patterns = [
            r"Traceback \(most recent call last\)",
            r"SyntaxError:",
            r"IndentationError:",
            r"ImportError:",
            r"ModuleNotFoundError:",
            r"NameError:",
            r"TypeError:",
            r"ValueError:",
            r"AttributeError:",
            r"FileNotFoundError:",
            r"KeyError:",
            r"RuntimeError:",
            r"Error:",
            r"FAILED",
            r"error\[",
        ]

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests on the generated project."""
        import logging

        logger = logging.getLogger(f"jarvis.agents.{self.name}")
        logger.info("▶  %s started", self.name)

        project_path = Path(context.get("project_path", ""))
        if not project_path.exists():
            context["test_result"] = {
                "success": False,
                "errors": ["Project path does not exist"],
                "stdout": "",
                "stderr": "",
            }
            return context

        errors: List[str] = []
        all_stdout = ""
        all_stderr = ""

        # ------------------------------------------------------------------
        # Step 1: Check that key files exist
        # ------------------------------------------------------------------
        generated_files = context.get("generated_files", {})
        for rel_path in generated_files:
            full = project_path / rel_path
            if not full.exists():
                errors.append(f"Missing file: {rel_path}")

        # ------------------------------------------------------------------
        # Step 2: Syntax-check all .py files
        # ------------------------------------------------------------------
        py_files = list(project_path.rglob("*.py"))
        for py_file in py_files:
            returncode, stdout, stderr = self.executor.run_command(
                f'"{self._python()}" -m py_compile "{py_file}"',
                cwd=project_path,
                timeout=self.timeout,
            )
            if returncode != 0:
                errors.append(f"Syntax error in {py_file.name}: {stderr.strip()}")
            all_stdout += stdout
            all_stderr += stderr

        # ------------------------------------------------------------------
        # Step 3: Try importing the main app module
        # ------------------------------------------------------------------
        app_main = project_path / "app" / "main.py"
        if app_main.exists():
            returncode, stdout, stderr = self.executor.run_command(
                f'"{self._python()}" -c "import sys; sys.path.insert(0, \'.\'); import app.main"',
                cwd=project_path,
                timeout=self.timeout,
            )
            if returncode != 0:
                errors.append(f"Import error: {stderr.strip()}")
            all_stdout += stdout
            all_stderr += stderr

        # ------------------------------------------------------------------
        # Step 4: Scan all output for error patterns
        # ------------------------------------------------------------------
        combined = all_stdout + all_stderr
        detected = self._detect_errors(combined)
        for err in detected:
            if err not in errors:
                errors.append(err)

        success = len(errors) == 0

        context["test_result"] = {
            "success": success,
            "errors": errors,
            "stdout": all_stdout[-2000:] if all_stdout else "",
            "stderr": all_stderr[-2000:] if all_stderr else "",
        }

        if success:
            logger.info("✅  %s: all checks passed", self.name)
        else:
            logger.warning(
                "⚠️  %s: %d error(s) detected", self.name, len(errors)
            )

        return context

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _detect_errors(self, text: str) -> List[str]:
        """Scan text for known error patterns."""
        found: List[str] = []
        for pattern in self._error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Get the line containing the match for context
                for match in matches[:3]:  # Limit to 3 per pattern
                    for line in text.splitlines():
                        if match in line:
                            found.append(line.strip()[:200])
                            break
        return found

    @staticmethod
    def _python() -> str:
        """Return the path to the current Python interpreter."""
        import sys

        return sys.executable
