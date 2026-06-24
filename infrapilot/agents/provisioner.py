"""Provisioner agent — turns declarative intent into live infrastructure."""

from __future__ import annotations

from infrapilot.agents.base import Agent
from infrapilot.llm import LLMClient


def Provisioner(llm: LLMClient | None = None) -> Agent:
    return Agent(
        role="Infrastructure Provisioner",
        goal="Provision the declared desired state safely and idempotently with Terraform.",
        backstory=(
            "A platform engineer who treats infrastructure as code and never "
            "applies a change without reviewing the plan first."
        ),
        tools=["terraform_provision"],
        llm=llm,
    )
