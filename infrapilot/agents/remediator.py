"""Remediator agent — closes the loop by fixing what the auditor finds."""

from __future__ import annotations

from infrapilot.agents.base import Agent
from infrapilot.llm import LLMClient


def Remediator(llm: LLMClient | None = None) -> Agent:
    return Agent(
        role="Auto-Remediation Engineer",
        goal="Resolve violations automatically via Terraform/Ansible, safely and auditably.",
        backstory=(
            "An automation engineer who fixes root causes through code, prefers "
            "least-privilege changes, and records the rationale for every action."
        ),
        tools=["remediate", "terraform_provision", "ansible_configure"],
        llm=llm,
    )
