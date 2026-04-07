"""
Jarvis v6 - CLI Entry Point
=============================
Run from the command line:
    python main.py "Build a blog website"
"""

from __future__ import annotations

import logging
import sys

from config import config
from core.ai_engine import AIEngine
from core.task_manager import TaskManager


# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------
def setup_logging() -> None:
    """Configure structured logging to console."""
    fmt = "%(asctime)s │ %(name)-28s │ %(levelname)-5s │ %(message)s"
    datefmt = "%H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# ------------------------------------------------------------------
# Banner
# ------------------------------------------------------------------
BANNER = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    ██╗   ██╗ ██████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██║   ██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗    ██║   ██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ╚██╗ ██╔╝██╔═══╝
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║     ╚████╔╝ ╚██████╗
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝      ╚═══╝   ╚═════╝
          Autonomous Software Builder AI   ·   v6.0
"""


# ------------------------------------------------------------------
# CLI progress callback
# ------------------------------------------------------------------
def cli_progress(agent: str, message: str, step: int, total: int) -> None:
    bar_len = 30
    filled = int(bar_len * (step + 1) / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = int(100 * (step + 1) / total)
    print(f"\r  [{bar}] {pct:3d}%  {agent}: {message}", end="", flush=True)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main() -> None:
    setup_logging()
    print(BANNER)
    print(config.display())
    print()

    # Get user idea from CLI args or prompt
    if len(sys.argv) > 1:
        user_idea = " ".join(sys.argv[1:])
    else:
        print("Enter your software idea (then press Enter):\n")
        user_idea = input("  > ").strip()

    if not user_idea:
        print("\n❌ No idea provided. Exiting.")
        sys.exit(1)

    print(f"\n🚀 Building: \"{user_idea}\"\n")
    print("=" * 60)

    # Build
    ai_engine = AIEngine(config)
    manager = TaskManager(config, ai_engine=ai_engine, on_progress=cli_progress)

    try:
        result = manager.build_project(user_idea)
    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user.")
        sys.exit(1)

    # Results
    print("\n\n" + "=" * 60)

    if result.success:
        print("✅  BUILD SUCCESSFUL")
    else:
        print("⚠️  BUILD COMPLETED WITH WARNINGS")

    print(f"   Project : {result.project_name}")
    print(f"   Path    : {result.project_path}")
    print(f"   Files   : {result.files_created}")
    print(f"   Time    : {result.total_time:.1f}s")

    if result.errors:
        print(f"\n⚠️  {len(result.errors)} warning(s):")
        for err in result.errors:
            print(f"   • {err}")

    print("\n📋 Pipeline Steps:")
    for step in result.steps:
        icon = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(step.status, "⏳")
        print(f"   {icon} {step.agent_name:<22} {step.message}")

    print("\n" + "=" * 60)
    print(f"📂 Project created at: {result.project_path}")
    print("🎉 Done!")


if __name__ == "__main__":
    main()
