"""
Jarvis v6 - Base Agent
=======================
Abstract base class that every agent inherits.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from core.ai_engine import AIEngine

logger = logging.getLogger("jarvis.agents")


class BaseAgent(ABC):
    """Abstract base for all Jarvis agents."""

    def __init__(self, ai_engine: AIEngine, name: str) -> None:
        self.ai = ai_engine
        self.name = name
        self.logger = logging.getLogger(f"jarvis.agents.{name}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent and return updated context.

        Handles logging, timing, and error wrapping.
        """
        self.logger.info("▶  %s started", self.name)
        start = time.time()

        try:
            prompt = self._build_prompt(context)
            system_prompt = self._system_prompt()

            raw_response = self.ai.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                expect_json=self._expect_json(),
            )

            result = self._parse_response(raw_response, context)
            elapsed = time.time() - start
            self.logger.info("✅  %s completed in %.1fs", self.name, elapsed)
            return result

        except Exception as exc:
            elapsed = time.time() - start
            self.logger.error(
                "❌  %s failed after %.1fs: %s", self.name, elapsed, exc
            )
            raise

    # ------------------------------------------------------------------
    # Abstract methods (must be implemented by each agent)
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build the LLM prompt from the pipeline context."""

    @abstractmethod
    def _parse_response(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM output and merge into context."""

    # ------------------------------------------------------------------
    # Overridable defaults
    # ------------------------------------------------------------------

    def _system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        return (
            "You are Jarvis, an expert software engineer AI. "
            "You generate clean, production-quality code. "
            "Always respond with valid JSON when asked to."
        )

    def _expect_json(self) -> bool:
        """Whether the response should be parsed as JSON."""
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def safe_json_loads(text: str) -> Any:
        """Parse JSON with a helpful error message."""
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("JSON parse error: %s\nRaw text:\n%s", exc, text[:500])
            # Return a minimal fallback so the pipeline doesn't crash
            return {"error": f"JSON parse failed: {exc}", "raw": text[:1000]}
