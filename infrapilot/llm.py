"""Optional LLM reasoning layer.

InfraPilot runs fully deterministically without any API key. When
``ANTHROPIC_API_KEY`` is set (and the ``anthropic`` package is installed), the
agents call an LLM to triage anomalies and to justify remediation choices —
the value-add of an *agentic* system over a static rules engine.

Default model is configurable via ``INFRAPILOT_MODEL`` (default:
``claude-sonnet-4-6``).
"""

from __future__ import annotations

import os


class LLMClient:
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("INFRAPILOT_MODEL", "claude-sonnet-4-6")
        self._client = None
        self._enabled = False
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                import anthropic  # noqa: PLC0415 - optional dependency

                self._client = anthropic.Anthropic(api_key=api_key)
                self._enabled = True
            except ImportError:
                self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def reason(self, system: str, prompt: str, *, max_tokens: int = 400) -> str | None:
        """Return the model's text, or ``None`` if the LLM is unavailable."""
        if not self._enabled or self._client is None:
            return None
        try:
            message = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in message.content if block.type == "text")
        except Exception:  # pragma: no cover - network/credential failures are non-fatal
            return None
