"""
Jarvis v6 - Central Configuration
==================================
Loads settings from .env and exposes them as a typed dataclass.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ------------------------------------------------------------------
# Resolve project root (the directory containing this file)
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent

# Load .env from project root
_env_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_env_path)


# ------------------------------------------------------------------
# Configuration dataclass
# ------------------------------------------------------------------
@dataclass
class JarvisConfig:
    """Immutable configuration for the Jarvis v6 system."""

    # AI backend: "ollama" or "huggingface"
    ai_backend: str = "ollama"

    # Ollama
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_base_url: str = "http://localhost:11434"

    # HuggingFace
    hf_model: str = "microsoft/Phi-3-mini-4k-instruct"

    # Generation
    max_tokens: int = 2048
    temperature: float = 0.2

    # Paths
    projects_dir: str = "generated_projects"

    # Testing
    test_timeout: int = 30
    max_fix_iterations: int = 3

    # Derived (set in __post_init__)
    projects_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.projects_path = PROJECT_ROOT / self.projects_dir
        self.projects_path.mkdir(parents=True, exist_ok=True)

    def display(self) -> str:
        """Return a human-readable summary of the active configuration."""
        lines = [
            "╔══════════════════════════════════════╗",
            "║       Jarvis v6 – Configuration      ║",
            "╠══════════════════════════════════════╣",
            f"║  Backend     : {self.ai_backend:<21}║",
        ]
        if self.ai_backend == "ollama":
            lines.append(f"║  Model       : {self.ollama_model:<21}║")
            lines.append(f"║  Ollama URL  : {self.ollama_base_url:<21}║")
        else:
            lines.append(f"║  Model       : {self.hf_model:<21}║")
        lines += [
            f"║  Max Tokens  : {str(self.max_tokens):<21}║",
            f"║  Temperature : {str(self.temperature):<21}║",
            f"║  Projects    : {self.projects_dir:<21}║",
            "╚══════════════════════════════════════╝",
        ]
        return "\n".join(lines)


# ------------------------------------------------------------------
# Build config from environment variables
# ------------------------------------------------------------------
def load_config() -> JarvisConfig:
    """Create a JarvisConfig from the current environment."""
    return JarvisConfig(
        ai_backend=os.getenv("AI_BACKEND", "ollama").lower().strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        hf_model=os.getenv("HF_MODEL", "microsoft/Phi-3-mini-4k-instruct"),
        max_tokens=int(os.getenv("MAX_TOKENS", "2048")),
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        projects_dir=os.getenv("PROJECTS_DIR", "generated_projects"),
        test_timeout=int(os.getenv("TEST_TIMEOUT", "30")),
        max_fix_iterations=int(os.getenv("MAX_FIX_ITERATIONS", "3")),
    )


# Singleton config instance
config = load_config()


# ------------------------------------------------------------------
# Quick self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    print(config.display())
    print(f"\nProjects directory: {config.projects_path}")
    print("✅ Configuration loaded successfully.")
