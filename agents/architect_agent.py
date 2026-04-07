"""
Jarvis v6 - Architect Agent
=============================
Designs the software architecture: folder structure, components, and data flow.
"""

from __future__ import annotations

from typing import Any, Dict

from agents.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):
    """Design the software architecture for the planned project."""

    def __init__(self, ai_engine, name: str = "ArchitectAgent") -> None:
        super().__init__(ai_engine, name)

    def _system_prompt(self) -> str:
        return (
            "You are a senior software architect. "
            "Design clean, modular architectures for web applications. "
            "Respond ONLY with a valid JSON object."
        )

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        project_name = context.get("project_name", "project")
        description = context.get("description", "")
        tasks = context.get("tasks", [])
        tech_stack = context.get("tech_stack", {})
        tasks_str = "\n".join(f"  - {t}" for t in tasks)

        return f"""Design the software architecture for this project.

Project: {project_name}
Description: {description}
Tech Stack: {tech_stack}
Tasks:
{tasks_str}

Respond with this exact JSON structure:
{{
    "folder_structure": {{
        "backend": [
            "app/__init__.py",
            "app/main.py",
            "app/models.py",
            "app/routes.py",
            "app/database.py",
            "requirements.txt"
        ],
        "frontend": [
            "static/index.html",
            "static/css/style.css",
            "static/js/app.js"
        ]
    }},
    "architecture_notes": "Brief description of the architecture pattern",
    "components": [
        {{
            "name": "ComponentName",
            "type": "backend|frontend|database",
            "description": "What this component does",
            "files": ["path/to/file.py"]
        }}
    ],
    "api_endpoints": [
        {{
            "method": "GET|POST|PUT|DELETE",
            "path": "/api/endpoint",
            "description": "What this endpoint does"
        }}
    ]
}}

Design a clean, modular architecture. Keep it practical and buildable."""

    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = self.safe_json_loads(response)

        context["folder_structure"] = data.get(
            "folder_structure",
            {
                "backend": [
                    "app/__init__.py",
                    "app/main.py",
                    "app/models.py",
                    "app/routes.py",
                    "app/database.py",
                    "requirements.txt",
                ],
                "frontend": [
                    "static/index.html",
                    "static/css/style.css",
                    "static/js/app.js",
                ],
            },
        )
        context["architecture_notes"] = data.get("architecture_notes", "")
        context["components"] = data.get("components", [])
        context["api_endpoints"] = data.get("api_endpoints", [])

        self.logger.info(
            "Architecture designed: %d components, %d endpoints",
            len(context["components"]),
            len(context["api_endpoints"]),
        )
        return context
