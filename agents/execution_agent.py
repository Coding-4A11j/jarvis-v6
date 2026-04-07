"""
Jarvis v6 - Execution Agent
==============================
Creates project folders, writes files to disk, and runs shell commands.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("jarvis.agents.ExecutionAgent")


class ExecutionAgent:
    """Handles file system operations and command execution.

    Unlike other agents, this does NOT call the LLM.
    It takes the generated files and physically creates them on disk.
    """

    def __init__(self, name: str = "ExecutionAgent") -> None:
        self.name = name
        self.logger = logger

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create the project on disk from context['generated_files']."""
        self.logger.info("▶  %s started", self.name)

        project_path = Path(context.get("project_path", ""))
        if not project_path:
            raise ValueError("No 'project_path' in context")

        generated_files = context.get("generated_files", {})
        if not generated_files:
            self.logger.warning("No generated files to write")
            context["execution_result"] = {"files_created": 0, "errors": []}
            return context

        created = []
        errors = []

        for rel_path, content in generated_files.items():
            try:
                full_path = project_path / rel_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
                created.append(str(rel_path))
                self.logger.info("  📄 Created: %s", rel_path)
            except Exception as exc:
                error_msg = f"Failed to create {rel_path}: {exc}"
                errors.append(error_msg)
                self.logger.error("  ❌ %s", error_msg)

        context["execution_result"] = {
            "files_created": len(created),
            "files": created,
            "errors": errors,
        }

        self.logger.info(
            "✅  %s completed: %d files created, %d errors",
            self.name,
            len(created),
            len(errors),
        )
        return context

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    @staticmethod
    def create_directory(path: Path) -> None:
        """Create a directory (and parents) if it doesn't exist."""
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write_file(path: Path, content: str) -> None:
        """Write content to a file, creating parent dirs as needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def run_command(
        cmd: str,
        cwd: Optional[Path] = None,
        timeout: int = 60,
    ) -> Tuple[int, str, str]:
        """Run a shell command and return (returncode, stdout, stderr).

        Args:
            cmd: The command string.
            cwd: Working directory.
            timeout: Max seconds to wait.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        logger.info("  🖥  Running: %s", cmd)
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as exc:
            return -1, "", str(exc)

    @staticmethod
    def get_project_tree(path: Path, prefix: str = "", max_depth: int = 4) -> str:
        """Generate a text-based directory tree string."""
        if max_depth <= 0:
            return prefix + "...\n"

        lines: List[str] = []
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return prefix + "[permission denied]\n"

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir() and not entry.name.startswith("."):
                extension = "    " if is_last else "│   "
                subtree = ExecutionAgent.get_project_tree(
                    entry, prefix + extension, max_depth - 1
                )
                if subtree:
                    lines.append(subtree.rstrip("\n"))

        return "\n".join(lines)
