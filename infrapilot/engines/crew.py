"""CrewAI orchestration engine (optional extra: ``pip install infra-pilot[crewai]``).

Maps the same agent crew and tools used by the native engine onto a CrewAI
``Crew`` running a sequential process. Requires ``crewai`` and an
``ANTHROPIC_API_KEY``; the model defaults to ``anthropic/claude-sonnet-4-6``.

This module is imported lazily by :func:`infrapilot.engines.get_engine` so the
core package stays dependency-light.
"""

from __future__ import annotations

import json
import os

from infrapilot.llm import LLMClient
from infrapilot.models import ComplianceResult, PipelineResult
from infrapilot.tools import (
    AnsibleTool,
    ComplianceTool,
    MonitoringTool,
    RemediationTool,
    TerraformTool,
)


def _require_crewai():
    try:
        from crewai import Agent, Crew, Process, Task  # noqa: PLC0415
        from crewai.tools import tool  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "CrewAI engine requires the 'crewai' extra. Install with: "
            "pip install 'infra-pilot[crewai]'"
        ) from exc
    return Agent, Crew, Process, Task, tool


class CrewAIEngine:
    """Thin adapter; the heavy lifting still lives in the shared tools."""

    name = "crewai"

    def __init__(self, *, simulate: bool = False, llm: LLMClient | None = None) -> None:
        self.simulate = simulate
        self.llm = llm or LLMClient()
        self.terraform = TerraformTool()
        self.ansible = AnsibleTool()
        self.monitoring = MonitoringTool()
        self.compliance = ComplianceTool()
        self.remediation = RemediationTool(self.terraform, self.ansible)

    def _build_crew(self):
        Agent, Crew, Process, Task, tool = _require_crewai()
        model = os.getenv("INFRAPILOT_MODEL", "anthropic/claude-sonnet-4-6")

        # --- wrap the shared tools as CrewAI tools --------------------------
        @tool("terraform_provision")
        def terraform_provision() -> str:
            """Provision the declared infrastructure with Terraform and return the resources."""
            resources, _ = self.terraform.apply()
            return json.dumps([r.model_dump() for r in resources])

        @tool("monitoring_query")
        def monitoring_query() -> str:
            """Query telemetry and return detected anomalies as JSON."""
            return json.dumps(self.monitoring.detect_anomalies())

        @tool("compliance_audit")
        def compliance_audit() -> str:
            """Audit the provisioned resources against policy-as-code; return violations."""
            resources, _ = self.terraform.apply()
            result = self.compliance.evaluate(resources)
            return result.model_dump_json()

        provisioner = Agent(
            role="Infrastructure Provisioner",
            goal="Provision the declared desired state with Terraform.",
            backstory="A platform engineer who treats infrastructure as code.",
            tools=[terraform_provision],
            llm=model,
            verbose=True,
        )
        observer = Agent(
            role="Observability Engineer",
            goal="Detect and triage anomalies in telemetry.",
            backstory="An SRE who separates signal from noise.",
            tools=[monitoring_query],
            llm=model,
            verbose=True,
        )
        auditor = Agent(
            role="Security & Compliance Auditor",
            goal="Validate every resource against security and governance policy.",
            backstory="A cloud security engineer who prioritises by blast radius.",
            tools=[compliance_audit],
            llm=model,
            verbose=True,
        )

        tasks = [
            Task(
                description="Provision the infrastructure and report what was created.",
                expected_output="A list of provisioned resources.",
                agent=provisioner,
            ),
            Task(
                description="Query telemetry and summarise any health anomalies.",
                expected_output="A triaged list of anomalies.",
                agent=observer,
            ),
            Task(
                description="Audit all resources for policy violations and rank them by severity.",
                expected_output="A prioritised list of violations with remediation hints.",
                agent=auditor,
            ),
        ]
        return Crew(
            agents=[provisioner, observer, auditor],
            tasks=tasks,
            process=Process.sequential,
        )

    def run(self, *, auto_remediate: bool = True) -> PipelineResult:
        crew = self._build_crew()
        crew.kickoff()
        # The crew produces the narrative; we still compute the structured result
        # from the shared tools so callers get a typed, comparable PipelineResult.
        resources, _ = self.terraform.apply()
        compliance: ComplianceResult = self.compliance.evaluate(resources)
        result = PipelineResult(
            engine=self.name,
            llm_enabled=self.llm.enabled,
            resources=resources,
            compliance=compliance,
        )
        result.add_stage("crewai", summary="CrewAI sequential crew completed")
        return result
