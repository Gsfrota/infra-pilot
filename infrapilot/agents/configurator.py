"""Configurator agent — converges OS/app configuration with Ansible."""

from __future__ import annotations

from infrapilot.agents.base import Agent
from infrapilot.llm import LLMClient


def Configurator(llm: LLMClient | None = None) -> Agent:
    return Agent(
        role="Configuration Manager",
        goal="Bring every host to its target configuration using Ansible playbooks.",
        backstory=(
            "An automation specialist who codifies golden configurations and "
            "enforces them continuously to prevent drift."
        ),
        tools=["ansible_configure"],
        llm=llm,
    )
