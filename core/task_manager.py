"""
Jarvis v6 - Task Manager
==========================
Orchestrates the full multi-agent pipeline from idea → working project.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agents.architect_agent import ArchitectAgent
from agents.backend_agent import BackendAgent
from agents.database_agent import DatabaseAgent
from agents.execution_agent import ExecutionAgent
from agents.frontend_agent import FrontendAgent
from agents.improvement_agent import ImprovementAgent
from agents.planner_agent import PlannerAgent
from agents.testing_agent import TestingAgent
from core.ai_engine import AIEngine

logger = logging.getLogger("jarvis.task_manager")


# ------------------------------------------------------------------
# Data classes for results
# ------------------------------------------------------------------

@dataclass
class StepResult:
    """Result of a single pipeline step."""
    agent_name: str
    status: str  # "success", "warning", "error"
    message: str
    elapsed: float = 0.0


@dataclass
class ProjectResult:
    """Final result of the full pipeline."""
    success: bool
    project_name: str
    project_path: str
    steps: List[StepResult] = field(default_factory=list)
    files_created: int = 0
    errors: List[str] = field(default_factory=list)
    total_time: float = 0.0


# ------------------------------------------------------------------
# Pipeline definition
# ------------------------------------------------------------------

PIPELINE_STEPS = [
    ("PlannerAgent", "Planning project…"),
    ("ArchitectAgent", "Designing architecture…"),
    ("DatabaseAgent", "Creating database schema…"),
    ("BackendAgent", "Generating backend APIs…"),
    ("FrontendAgent", "Generating frontend UI…"),
    ("ExecutionAgent", "Writing files to disk…"),
    ("TestingAgent", "Running tests…"),
    ("ImprovementLoop", "Fixing errors (if any)…"),
]


# ------------------------------------------------------------------
# Task Manager
# ------------------------------------------------------------------

class TaskManager:
    """Orchestrate the full Jarvis generation pipeline."""

    def __init__(
        self,
        config,
        ai_engine: Optional[AIEngine] = None,
        on_progress: Optional[Callable[[str, str, int, int], None]] = None,
    ) -> None:
        """
        Args:
            config: JarvisConfig instance.
            ai_engine: Shared AIEngine (created if None).
            on_progress: Callback(agent_name, message, step_index, total_steps).
        """
        self.config = config
        self.ai = ai_engine or AIEngine(config)
        self.on_progress = on_progress

        # Instantiate agents
        self.planner = PlannerAgent(self.ai)
        self.architect = ArchitectAgent(self.ai)
        self.backend = BackendAgent(self.ai)
        self.frontend = FrontendAgent(self.ai)
        self.database = DatabaseAgent(self.ai)
        self.executor = ExecutionAgent()
        self.tester = TestingAgent(timeout=config.test_timeout)
        self.improver = ImprovementAgent(self.ai)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def build_project(self, user_idea: str) -> ProjectResult:
        """Run the full pipeline: idea → working project.

        Args:
            user_idea: The user's natural-language software idea.

        Returns:
            A ProjectResult with status, files, and errors.
        """
        total_start = time.time()
        total_steps = len(PIPELINE_STEPS)
        steps: List[StepResult] = []

        # Initial context
        context: Dict[str, Any] = {
            "user_idea": user_idea,
            "generated_files": {},
        }

        # -------------------------------------------------------
        # Step 1 – Planner
        # -------------------------------------------------------
        step_result = self._run_step(
            self.planner, context, 0, total_steps
        )
        steps.append(step_result)
        if step_result.status == "error":
            return self._make_result(False, context, steps, total_start)

        # Set project path
        project_name = context.get("project_name", "my-project")
        project_path = self.config.projects_path / project_name
        context["project_path"] = project_path

        # -------------------------------------------------------
        # Step 2 – Architect
        # -------------------------------------------------------
        step_result = self._run_step(
            self.architect, context, 1, total_steps
        )
        steps.append(step_result)

        # -------------------------------------------------------
        # Step 3 – Database
        # -------------------------------------------------------
        step_result = self._run_step(
            self.database, context, 2, total_steps
        )
        steps.append(step_result)

        # -------------------------------------------------------
        # Step 4 – Backend
        # -------------------------------------------------------
        step_result = self._run_step(
            self.backend, context, 3, total_steps
        )
        steps.append(step_result)

        # -------------------------------------------------------
        # Step 5 – Frontend
        # -------------------------------------------------------
        step_result = self._run_step(
            self.frontend, context, 4, total_steps
        )
        steps.append(step_result)

        # -------------------------------------------------------
        # Step 6 – Execution (write files to disk)
        # -------------------------------------------------------
        self._emit_progress("ExecutionAgent", "Writing files to disk…", 5, total_steps)
        start = time.time()
        try:
            context = self.executor.run(context)
            exec_result = context.get("execution_result", {})
            n_files = exec_result.get("files_created", 0)
            exec_errors = exec_result.get("errors", [])

            status = "success" if not exec_errors else "warning"
            steps.append(StepResult(
                "ExecutionAgent", status,
                f"{n_files} files created",
                time.time() - start,
            ))
        except Exception as exc:
            steps.append(StepResult(
                "ExecutionAgent", "error", str(exc), time.time() - start
            ))
            return self._make_result(False, context, steps, total_start)

        # -------------------------------------------------------
        # Step 7 – Testing
        # -------------------------------------------------------
        self._emit_progress("TestingAgent", "Running tests…", 6, total_steps)
        start = time.time()
        try:
            context = self.tester.run(context)
            test_result = context.get("test_result", {})
            test_success = test_result.get("success", False)
            test_errors = test_result.get("errors", [])

            status = "success" if test_success else "warning"
            steps.append(StepResult(
                "TestingAgent", status,
                f"{len(test_errors)} error(s)" if test_errors else "All checks passed",
                time.time() - start,
            ))
        except Exception as exc:
            steps.append(StepResult(
                "TestingAgent", "error", str(exc), time.time() - start
            ))

        # -------------------------------------------------------
        # Step 8 – Improvement Loop
        # -------------------------------------------------------
        test_result = context.get("test_result", {})
        if not test_result.get("success", True):
            self._emit_progress(
                "ImprovementLoop", "Fixing errors…", 7, total_steps
            )
            start = time.time()
            context = self._improvement_loop(context)
            loop_result = context.get("test_result", {})
            loop_success = loop_result.get("success", False)
            steps.append(StepResult(
                "ImprovementLoop",
                "success" if loop_success else "warning",
                "All fixes applied" if loop_success else "Some errors remain",
                time.time() - start,
            ))
        else:
            steps.append(StepResult(
                "ImprovementLoop", "success", "No fixes needed", 0.0
            ))

        # Final result
        final_success = context.get("test_result", {}).get("success", False)
        return self._make_result(final_success, context, steps, total_start)

    # ------------------------------------------------------------------
    # Improvement loop
    # ------------------------------------------------------------------

    def _improvement_loop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Re-try ImprovementAgent → ExecutionAgent → TestingAgent up to N times."""
        max_iters = self.config.max_fix_iterations

        for i in range(1, max_iters + 1):
            logger.info("Improvement iteration %d/%d", i, max_iters)

            # Let the LLM fix the code
            try:
                context = self.improver.run(context)
            except Exception as exc:
                logger.error("ImprovementAgent failed: %s", exc)
                break

            # Re-write fixed files
            try:
                context = self.executor.run(context)
            except Exception as exc:
                logger.error("ExecutionAgent failed during fix: %s", exc)
                break

            # Re-test
            try:
                context = self.tester.run(context)
            except Exception as exc:
                logger.error("TestingAgent failed during fix: %s", exc)
                break

            if context.get("test_result", {}).get("success", False):
                logger.info("✅ All errors fixed after %d iteration(s)", i)
                break
        else:
            logger.warning(
                "⚠️  Max improvement iterations (%d) reached", max_iters
            )

        return context

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run_step(
        self,
        agent,
        context: Dict[str, Any],
        step_idx: int,
        total: int,
    ) -> StepResult:
        """Run a single agent step with progress reporting."""
        name = agent.name
        desc = PIPELINE_STEPS[step_idx][1]
        self._emit_progress(name, desc, step_idx, total)

        start = time.time()
        try:
            context.update(agent.run(context))
            return StepResult(name, "success", desc, time.time() - start)
        except Exception as exc:
            return StepResult(name, "error", str(exc), time.time() - start)

    def _emit_progress(
        self, agent: str, msg: str, step: int, total: int
    ) -> None:
        """Send progress to the callback if registered."""
        logger.info("[%d/%d] %s – %s", step + 1, total, agent, msg)
        if self.on_progress:
            try:
                self.on_progress(agent, msg, step, total)
            except Exception:
                pass  # Never let a UI callback crash the pipeline

    @staticmethod
    def _make_result(
        success: bool,
        context: Dict[str, Any],
        steps: List[StepResult],
        start_time: float,
    ) -> ProjectResult:
        project_path = str(context.get("project_path", ""))
        exec_result = context.get("execution_result", {})
        test_result = context.get("test_result", {})

        return ProjectResult(
            success=success,
            project_name=context.get("project_name", "unknown"),
            project_path=project_path,
            steps=steps,
            files_created=exec_result.get("files_created", 0),
            errors=test_result.get("errors", []),
            total_time=time.time() - start_time,
        )
