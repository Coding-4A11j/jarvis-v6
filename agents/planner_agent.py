"""
Jarvis v6 - Planner Agent
==========================
Breaks a user's software idea into concrete development tasks.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Parse a high-level idea into a structured development plan."""

    def __init__(self, ai_engine, name: str = "PlannerAgent") -> None:
        super().__init__(ai_engine, name)

    def _system_prompt(self) -> str:
        return (
            "You are a senior software project planner. "
            "Given a software idea, break it down into clear, ordered development tasks. "
            "Respond ONLY with a valid JSON object. No explanation outside the JSON."
        )

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        idea = context.get("user_idea", "")
        return f"""Analyze this software project idea and create a development plan.

User Idea: "{idea}"

Respond with this exact JSON structure:
{{
    "project_name": "short-kebab-case-name",
    "description": "One paragraph describing the project",
    "tech_stack": {{
        "backend": "FastAPI",
        "frontend": "HTML/CSS/JavaScript",
        "database": "SQLite with SQLAlchemy"
    }},
    "tasks": [
        "Task 1 description",
        "Task 2 description",
        "Task 3 description"
    ],
    "features": [
        "Feature 1",
        "Feature 2"
    ]
}}

Make the tasks specific and actionable. Include 5-10 tasks covering:
- Database models
- Backend API routes
- Frontend pages
- Authentication (if relevant)
- Core business logic"""

    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = self.safe_json_loads(response)

        # Ensure required keys exist with defaults
        project_name = data.get("project_name", "my-project")
        # Sanitize project name
        project_name = re.sub(r"[^a-z0-9\-]", "-", project_name.lower().strip())
        project_name = re.sub(r"-+", "-", project_name).strip("-")

        context["project_name"] = project_name or "my-project"
        context["description"] = data.get("description", context.get("user_idea", ""))
        context["tech_stack"] = data.get(
            "tech_stack",
            {
                "backend": "FastAPI",
                "frontend": "HTML/CSS/JavaScript",
                "database": "SQLite with SQLAlchemy",
            },
        )
        context["tasks"] = data.get("tasks", ["Setup project structure"])
        context["features"] = data.get("features", [])

        self.logger.info(
            "Planned project '%s' with %d tasks",
            context["project_name"],
            len(context["tasks"]),
        )
        return context
