"""
Jarvis v6 - AI Engine
======================
Pluggable AI generation backend.
Supports Ollama (recommended) and HuggingFace Transformers.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

logger = logging.getLogger("jarvis.ai_engine")


class AIEngine:
    """Unified interface for local LLM generation."""

    def __init__(self, config) -> None:
        self.config = config
        self.backend = config.ai_backend  # "ollama" or "huggingface"
        self._hf_model = None
        self._hf_tokenizer = None
        logger.info("AIEngine initialised  backend=%s", self.backend)

    # ==================================================================
    # Public API
    # ==================================================================

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are Jarvis, an expert software engineer AI assistant.",
        expect_json: bool = False,
    ) -> str:
        """Generate text from the active backend.

        Args:
            prompt: The user/task prompt.
            system_prompt: System-level instruction.
            expect_json: If True, attempt to extract valid JSON from the response.

        Returns:
            The generated text (or JSON string if expect_json=True).
        """
        response = self._generate_with_retry(prompt, system_prompt)

        if expect_json:
            response = self._extract_json(response)

        return response

    # ==================================================================
    # Retry wrapper
    # ==================================================================

    def _generate_with_retry(
        self, prompt: str, system_prompt: str, max_retries: int = 3
    ) -> str:
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                if self.backend == "ollama":
                    return self._generate_ollama(prompt, system_prompt)
                elif self.backend == "huggingface":
                    return self._generate_hf(prompt, system_prompt)
                else:
                    raise ValueError(f"Unknown AI backend: {self.backend}")
            except Exception as exc:
                last_error = exc
                wait = 2 ** attempt
                logger.warning(
                    "Generation attempt %d/%d failed: %s – retrying in %ds",
                    attempt,
                    max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)

        raise RuntimeError(
            f"AI generation failed after {max_retries} attempts: {last_error}"
        )

    # ==================================================================
    # Ollama backend
    # ==================================================================

    def _generate_ollama(self, prompt: str, system_prompt: str) -> str:
        """Generate using the local Ollama server."""
        try:
            import ollama as ollama_lib
        except ImportError:
            raise ImportError(
                "The 'ollama' package is not installed. "
                "Run: pip install ollama"
            )

        client = ollama_lib.Client(host=self.config.ollama_base_url)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        response = client.chat(
            model=self.config.ollama_model,
            messages=messages,
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        )

        return response["message"]["content"]

    # ==================================================================
    # HuggingFace Transformers backend
    # ==================================================================

    def _generate_hf(self, prompt: str, system_prompt: str) -> str:
        """Generate using a HuggingFace Transformers model (loaded locally)."""
        self._ensure_hf_loaded()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        input_ids = self._hf_tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self._hf_model.device)

        outputs = self._hf_model.generate(
            input_ids,
            max_new_tokens=self.config.max_tokens,
            do_sample=True,
            temperature=max(self.config.temperature, 0.01),
        )

        generated_tokens = outputs[0][input_ids.shape[-1]:]
        return self._hf_tokenizer.decode(generated_tokens, skip_special_tokens=True)

    def _ensure_hf_loaded(self) -> None:
        """Lazy-load the HuggingFace model and tokenizer once."""
        if self._hf_model is not None:
            return

        logger.info("Loading HuggingFace model: %s …", self.config.hf_model)

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise ImportError(
                "The 'transformers' package is not installed. "
                "Run: pip install transformers accelerate torch"
            )

        self._hf_tokenizer = AutoTokenizer.from_pretrained(self.config.hf_model)
        self._hf_model = AutoModelForCausalLM.from_pretrained(
            self.config.hf_model,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
        )
        logger.info("HuggingFace model loaded successfully.")

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _extract_json(text: str) -> str:
        """Try to extract a valid JSON object or array from LLM output."""
        # Try direct parse first
        stripped = text.strip()
        try:
            json.loads(stripped)
            return stripped
        except json.JSONDecodeError:
            pass

        # Try to find JSON in code fences
        fence_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        match = re.search(fence_pattern, text)
        if match:
            candidate = match.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # Try to find first { ... } or [ ... ]
        for open_char, close_char in [("{", "}"), ("[", "]")]:
            start = text.find(open_char)
            if start == -1:
                continue
            depth = 0
            for i in range(start, len(text)):
                if text[i] == open_char:
                    depth += 1
                elif text[i] == close_char:
                    depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        break

        # Return raw text as fallback
        logger.warning("Could not extract valid JSON from AI response.")
        return stripped
