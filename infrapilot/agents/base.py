"""Base agent definition shared by every engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from infrapilot.llm import LLMClient


@dataclass
class Agent:
    """Role/goal/backstory triple — the contract every engine consumes."""

    role: str
    goal: str
    backstory: str
    tools: list[str] = field(default_factory=list)
    llm: LLMClient | None = None

    def think(self, prompt: str) -> str | None:
        """Optional LLM reasoning step; returns None when no LLM is configured."""
        if self.llm is None:
            return None
        system = f"You are the {self.role}. Goal: {self.goal}. {self.backstory}"
        return self.llm.reason(system, prompt)
