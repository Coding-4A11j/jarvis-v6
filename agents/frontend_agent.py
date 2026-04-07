"""
Jarvis v6 - Frontend Agent
============================
Generates HTML / CSS / JavaScript frontend code.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):
    """Generate complete frontend code (HTML/CSS/JS)."""

    def __init__(self, ai_engine, name: str = "FrontendAgent") -> None:
        super().__init__(ai_engine, name)

    def _system_prompt(self) -> str:
        return (
            "You are an expert frontend developer. "
            "Generate modern, responsive HTML/CSS/JavaScript code. "
            "Use clean design with a professional color scheme. "
            "Respond ONLY with valid JSON."
        )

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        project_name = context.get("project_name", "project")
        description = context.get("description", "")
        features = context.get("features", [])
        endpoints = context.get("api_endpoints", [])
        folder_struct = context.get("folder_structure", {})
        frontend_files = folder_struct.get("frontend", [])

        features_str = "\n".join(f"  - {f}" for f in features)
        endpoints_str = json.dumps(endpoints, indent=2) if endpoints else "[]"
        files_str = "\n".join(f"  - {f}" for f in frontend_files)

        return f"""Generate complete frontend code for this web application.

Project: {project_name}
Description: {description}

Features:
{features_str}

Backend API Endpoints available:
{endpoints_str}

Files to generate:
{files_str}

Generate each file with COMPLETE, working code. Respond with this JSON structure:
{{
    "files": {{
        "static/index.html": "full HTML code...",
        "static/css/style.css": "full CSS code...",
        "static/js/app.js": "full JavaScript code..."
    }}
}}

Requirements:
- Modern, responsive design with CSS Grid/Flexbox
- Professional dark theme with accent colors
- Use fetch() API to call backend endpoints
- Include loading states and error handling
- Mobile-responsive layout
- Use Google Fonts (Inter or Roboto)
- Smooth transitions and hover effects
- Include a navigation bar and footer
- Forms should have proper validation"""

    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = self.safe_json_loads(response)

        files = data.get("files", {})
        if not files:
            self.logger.warning("FrontendAgent returned no files, using fallback")
            files = self._fallback_frontend(context)

        if "generated_files" not in context:
            context["generated_files"] = {}
        context["generated_files"].update(files)

        self.logger.info("Generated %d frontend files", len(files))
        return context

    @staticmethod
    def _fallback_frontend(context: Dict[str, Any]) -> Dict[str, str]:
        """Minimal fallback frontend."""
        project_name = context.get("project_name", "project")
        title = project_name.replace("-", " ").title()
        return {
            "static/index.html": (
                '<!DOCTYPE html>\n'
                '<html lang="en">\n'
                '<head>\n'
                '    <meta charset="UTF-8">\n'
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                f'    <title>{title}</title>\n'
                '    <link rel="stylesheet" href="/static/css/style.css">\n'
                '    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">\n'
                '</head>\n'
                '<body>\n'
                '    <nav class="navbar">\n'
                f'        <h1>{title}</h1>\n'
                '    </nav>\n'
                '    <main class="container">\n'
                f'        <h2>Welcome to {title}</h2>\n'
                '        <p>Your application is running.</p>\n'
                '    </main>\n'
                '    <script src="/static/js/app.js"></script>\n'
                '</body>\n'
                '</html>\n'
            ),
            "static/css/style.css": (
                '*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }\n'
                'body { font-family: "Inter", sans-serif; background: #0f172a; color: #e2e8f0; }\n'
                '.navbar { background: #1e293b; padding: 1rem 2rem; border-bottom: 1px solid #334155; }\n'
                '.navbar h1 { font-size: 1.25rem; color: #38bdf8; }\n'
                '.container { max-width: 960px; margin: 2rem auto; padding: 0 1rem; }\n'
                'h2 { margin-bottom: 1rem; }\n'
            ),
            "static/js/app.js": (
                '"use strict";\n'
                'console.log("App loaded");\n'
            ),
        }
