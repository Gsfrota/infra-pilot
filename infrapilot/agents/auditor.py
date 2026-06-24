"""Compliance auditor agent — enforces policy-as-code governance."""

from __future__ import annotations

from infrapilot.agents.base import Agent
from infrapilot.llm import LLMClient


def ComplianceAuditor(llm: LLMClient | None = None) -> Agent:
    return Agent(
        role="Security & Compliance Auditor",
        goal="Validate every resource against security and governance policies.",
        backstory=(
            "A cloud security engineer who maps findings to controls and "
            "prioritises fixes by blast radius and severity."
        ),
        tools=["compliance_audit"],
        llm=llm,
    )
