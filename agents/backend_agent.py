"""
Jarvis v6 - Backend Agent
==========================
Generates FastAPI backend code based on the architecture plan.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agents.base_agent import BaseAgent


class BackendAgent(BaseAgent):
    """Generate complete FastAPI backend code."""

    def __init__(self, ai_engine, name: str = "BackendAgent") -> None:
        super().__init__(ai_engine, name)

    def _system_prompt(self) -> str:
        return (
            "You are an expert Python backend developer specializing in FastAPI. "
            "Generate clean, production-quality Python code. "
            "Always include proper imports, error handling, and type hints. "
            "Respond ONLY with valid JSON."
        )

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        project_name = context.get("project_name", "project")
        description = context.get("description", "")
        tasks = context.get("tasks", [])
        endpoints = context.get("api_endpoints", [])
        folder_struct = context.get("folder_structure", {})
        backend_files = folder_struct.get("backend", [])

        tasks_str = "\n".join(f"  - {t}" for t in tasks)
        endpoints_str = json.dumps(endpoints, indent=2) if endpoints else "[]"
        files_str = "\n".join(f"  - {f}" for f in backend_files)

        return f"""Generate the complete FastAPI backend code for this project.

Project: {project_name}
Description: {description}

Tasks:
{tasks_str}

API Endpoints to implement:
{endpoints_str}

Files to generate:
{files_str}

Generate each file with COMPLETE, working code. Respond with this JSON structure:
{{
    "files": {{
        "app/__init__.py": "# app package init",
        "app/main.py": "full code here...",
        "app/models.py": "full code here...",
        "app/routes.py": "full code here...",
        "app/database.py": "full code here...",
        "requirements.txt": "fastapi\\nuvicorn\\nsqlalchemy\\n..."
    }}
}}

Requirements:
- Use FastAPI with async routes
- Use SQLAlchemy for ORM with SQLite
- Include CORS middleware
- Add proper error handling with HTTPException
- Include a health check endpoint at GET /
- Mount static files from ../static for frontend
- Use Pydantic models for request/response validation
- Generate a requirements.txt with all needed packages"""

    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = self.safe_json_loads(response)

        files = data.get("files", {})
        if not files:
            self.logger.warning("BackendAgent returned no files, using fallback")
            files = self._fallback_backend(context)

        # Merge into context
        if "generated_files" not in context:
            context["generated_files"] = {}
        context["generated_files"].update(files)

        self.logger.info("Generated %d backend files", len(files))
        return context

    @staticmethod
    def _fallback_backend(context: Dict[str, Any]) -> Dict[str, str]:
        """Minimal fallback backend if LLM output is unusable."""
        project_name = context.get("project_name", "project")
        return {
            "app/__init__.py": '"""App package."""\n',
            "app/main.py": (
                'from fastapi import FastAPI\n'
                'from fastapi.middleware.cors import CORSMiddleware\n'
                'from fastapi.staticfiles import StaticFiles\n'
                'import os\n\n'
                f'app = FastAPI(title="{project_name}")\n\n'
                'app.add_middleware(\n'
                '    CORSMiddleware,\n'
                '    allow_origins=["*"],\n'
                '    allow_methods=["*"],\n'
                '    allow_headers=["*"],\n'
                ')\n\n'
                'static_dir = os.path.join(os.path.dirname(__file__), "..", "static")\n'
                'if os.path.isdir(static_dir):\n'
                '    app.mount("/static", StaticFiles(directory=static_dir), name="static")\n\n'
                '@app.get("/")\n'
                'async def root():\n'
                f'    return {{"message": "Welcome to {project_name}"}}\n\n'
                '@app.get("/health")\n'
                'async def health():\n'
                '    return {"status": "healthy"}\n'
            ),
            "app/database.py": (
                'from sqlalchemy import create_engine\n'
                'from sqlalchemy.orm import sessionmaker, declarative_base\n\n'
                'DATABASE_URL = "sqlite:///./app.db"\n'
                'engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})\n'
                'SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n'
                'Base = declarative_base()\n\n'
                'def get_db():\n'
                '    db = SessionLocal()\n'
                '    try:\n'
                '        yield db\n'
                '    finally:\n'
                '        db.close()\n'
            ),
            "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\npython-multipart\n",
        }
