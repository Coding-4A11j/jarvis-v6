"""
Jarvis v6 - Database Agent
============================
Generates database schemas, models, and migration helpers.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agents.base_agent import BaseAgent


class DatabaseAgent(BaseAgent):
    """Generate SQLAlchemy database models and helpers."""

    def __init__(self, ai_engine, name: str = "DatabaseAgent") -> None:
        super().__init__(ai_engine, name)

    def _system_prompt(self) -> str:
        return (
            "You are an expert database engineer. "
            "Design clean, normalized database schemas using SQLAlchemy ORM. "
            "Respond ONLY with valid JSON."
        )

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        project_name = context.get("project_name", "project")
        description = context.get("description", "")
        tasks = context.get("tasks", [])
        features = context.get("features", [])
        endpoints = context.get("api_endpoints", [])

        tasks_str = "\n".join(f"  - {t}" for t in tasks)
        features_str = "\n".join(f"  - {f}" for f in features)
        endpoints_str = json.dumps(endpoints, indent=2) if endpoints else "[]"

        return f"""Design and generate the database schema for this project.

Project: {project_name}
Description: {description}

Tasks:
{tasks_str}

Features:
{features_str}

API Endpoints:
{endpoints_str}

Respond with this exact JSON structure:
{{
    "files": {{
        "app/models.py": "full SQLAlchemy model code here..."
    }},
    "models": [
        {{
            "name": "User",
            "table": "users",
            "fields": [
                {{"name": "id", "type": "Integer", "primary_key": true}},
                {{"name": "username", "type": "String(50)", "unique": true}},
                {{"name": "email", "type": "String(120)", "unique": true}}
            ]
        }}
    ]
}}

Requirements:
- Use SQLAlchemy declarative_base (import Base from app.database)
- Include proper relationships between models
- Add created_at and updated_at timestamps
- Use appropriate column types and constraints
- Include __repr__ methods on each model
- Create all tables at the end of the file"""

    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = self.safe_json_loads(response)

        files = data.get("files", {})
        if not files:
            self.logger.warning("DatabaseAgent returned no files, using fallback")
            files = self._fallback_models(context)

        if "generated_files" not in context:
            context["generated_files"] = {}
        context["generated_files"].update(files)

        context["models"] = data.get("models", [])

        self.logger.info(
            "Generated %d database files, %d models",
            len(files),
            len(context["models"]),
        )
        return context

    @staticmethod
    def _fallback_models(context: Dict[str, Any]) -> Dict[str, str]:
        """Minimal fallback database models."""
        return {
            "app/models.py": (
                'from datetime import datetime\n'
                'from sqlalchemy import Column, Integer, String, DateTime, Text\n'
                'from app.database import Base, engine\n\n\n'
                'class User(Base):\n'
                '    __tablename__ = "users"\n\n'
                '    id = Column(Integer, primary_key=True, index=True)\n'
                '    username = Column(String(50), unique=True, nullable=False)\n'
                '    email = Column(String(120), unique=True, nullable=False)\n'
                '    created_at = Column(DateTime, default=datetime.utcnow)\n\n'
                '    def __repr__(self):\n'
                '        return f"<User(id={self.id}, username={self.username})>"\n\n\n'
                '# Create all tables\n'
                'Base.metadata.create_all(bind=engine)\n'
            ),
        }
