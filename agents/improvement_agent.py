"""
Jarvis v6 - Improvement Agent
================================
Analyzes errors from the TestingAgent and generates fixed code.
"""

from __future__ import annotations

from typing import Any, Dict

from agents.base_agent import BaseAgent


class ImprovementAgent(BaseAgent):
    """Feed errors back to the LLM and get corrected code."""

    def __init__(self, ai_engine, name: str = "ImprovementAgent") -> None:
        super().__init__(ai_engine, name)

    def _system_prompt(self) -> str:
        return (
            "You are an expert debugging engineer. "
            "Given error messages and the original code, fix ALL issues. "
            "Return ONLY the corrected files as valid JSON. "
            "Do NOT explain. Just return the fixed code."
        )

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        test_result = context.get("test_result", {})
        errors = test_result.get("errors", [])
        stderr = test_result.get("stderr", "")
        generated_files = context.get("generated_files", {})

        errors_str = "\n".join(f"  - {e}" for e in errors)
        stderr_snippet = stderr[-1500:] if stderr else "N/A"

        # Include the relevant source files
        files_str_parts = []
        for path, content in generated_files.items():
            # Only include Python files and the most relevant ones
            if path.endswith((".py", ".txt", ".html", ".css", ".js")):
                # Truncate very large files
                truncated = content[:3000] if len(content) > 3000 else content
                files_str_parts.append(f"--- {path} ---\n{truncated}")

        files_str = "\n\n".join(files_str_parts)

        return f"""The generated project has errors. Fix them.

ERRORS:
{errors_str}

STDERR:
{stderr_snippet}

CURRENT FILES:
{files_str}

Respond with this JSON structure containing ONLY the files that need fixing:
{{
    "files": {{
        "path/to/file.py": "complete corrected file content...",
        "path/to/other.py": "complete corrected file content..."
    }},
    "changes_made": [
        "Description of fix 1",
        "Description of fix 2"
    ]
}}

Rules:
- Fix ALL errors listed above
- Return the COMPLETE file contents (not just the changed lines)
- Ensure all imports are correct
- Ensure all syntax is valid Python
- Do not remove any existing functionality"""

    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = self.safe_json_loads(response)

        fixed_files = data.get("files", {})
        changes_made = data.get("changes_made", [])

        if fixed_files:
            # Merge fixes into generated_files
            if "generated_files" not in context:
                context["generated_files"] = {}
            context["generated_files"].update(fixed_files)

            self.logger.info(
                "Fixed %d file(s): %s",
                len(fixed_files),
                ", ".join(fixed_files.keys()),
            )
            for change in changes_made:
                self.logger.info("  🔧 %s", change)
        else:
            self.logger.warning("ImprovementAgent returned no fixes")

        context["changes_made"] = changes_made
        return context
