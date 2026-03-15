"""
LLM Provider Abstraction Layer
-------------------------------
Wraps OpenAI-compatible and Anthropic APIs behind a single
`generate()` interface so the rest of CortexOS stays provider-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cortex_core.config import LLMConfig


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""

    text: str
    model: str
    usage: dict[str, int]
    raw: Any = None


class LLMProvider:
    """Unified LLM interface."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client: Any = None

    # ------------------------------------------------------------------ core

    def generate(
        self,
        prompt: str,
        *,
        system: str = "You are CortexOS, a thinking engine that helps knowledge workers.",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send a prompt and return a normalised response."""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        if self.config.provider == "anthropic":
            return self._call_anthropic(prompt, system, temp, tokens)
        # Default: OpenAI-compatible
        return self._call_openai(prompt, system, temp, tokens)

    # -------------------------------------------------------- OpenAI backend

    def _call_openai(self, prompt: str, system: str, temperature: float, max_tokens: int) -> LLMResponse:
        try:
            import openai
        except ImportError:
            return self._fallback(prompt)

        client = openai.OpenAI(
            api_key=self.config.resolve_api_key(),
            base_url=self.config.base_url,
        )
        resp = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = resp.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
            },
            raw=resp,
        )

    # ------------------------------------------------------ Anthropic backend

    def _call_anthropic(self, prompt: str, system: str, temperature: float, max_tokens: int) -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            return self._fallback(prompt)

        client = anthropic.Anthropic(api_key=self.config.resolve_api_key())
        resp = client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        text = resp.content[0].text if resp.content else ""
        return LLMResponse(
            text=text,
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.input_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.output_tokens if resp.usage else 0,
            },
            raw=resp,
        )

    # -------------------------------------------------------- offline fallback

    @staticmethod
    def _fallback(prompt: str) -> LLMResponse:
        """Simple echo fallback when no SDK is installed."""
        return LLMResponse(
            text=f"[CortexOS offline] Received prompt ({len(prompt)} chars). "
            "Install openai or anthropic package for full LLM support.",
            model="fallback",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )
