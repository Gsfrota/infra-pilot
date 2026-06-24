"""Native multi-agent orchestration engine.

Runs the full ops loop — provision -> configure -> observe -> audit -> remediate
-> re-audit — coordinating the agent crew and their tools. Has no heavy runtime
dependencies, so it always runs (laptop, CI, container) and is the engine the
test suite exercises.
"""

from __future__ import annotations

from infrapilot.agents import (
    ComplianceAuditor,
    Configurator,
    Observer,
    Provisioner,
    Remediator,
)
from infrapilot.executors import CommandExecutor
from infrapilot.llm import LLMClient
from infrapilot.models import PipelineResult
from infrapilot.tools import (
    AnsibleTool,
    ComplianceTool,
    MonitoringTool,
    RemediationTool,
    TerraformTool,
)


class NativeEngine:
    name = "native"

    def __init__(self, *, simulate: bool = False, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        executor = CommandExecutor(force_simulate=simulate)
        self.terraform = TerraformTool(executor)
        self.ansible = AnsibleTool(executor)
        self.monitoring = MonitoringTool()
        self.compliance = ComplianceTool()
        self.remediation = RemediationTool(self.terraform, self.ansible)
        # agent crew (role/goal/tools), wired with the optional LLM
        self.provisioner = Provisioner(self.llm)
        self.configurator = Configurator(self.llm)
        self.observer = Observer(self.llm)
        self.auditor = ComplianceAuditor(self.llm)
        self.remediator = Remediator(self.llm)

    def run(self, *, auto_remediate: bool = True) -> PipelineResult:
        result = PipelineResult(engine=self.name, llm_enabled=self.llm.enabled)

        # 1. Provision -----------------------------------------------------
        resources, apply_res = self.terraform.apply()
        result.resources = resources
        result.add_stage(
            "provision",
            summary=f"{len(resources)} resources provisioned"
            + (" (simulated)" if apply_res.simulated else ""),
            simulated=apply_res.simulated,
        )

        # 2. Configure -----------------------------------------------------
        ans_res = self.ansible.run_playbook()
        result.add_stage(
            "configure",
            summary="configuration applied" + (" (simulated)" if ans_res.simulated else ""),
            simulated=ans_res.simulated,
        )

        # 3. Observe -------------------------------------------------------
        anomalies = self.monitoring.detect_anomalies()
        result.add_stage(
            "observe",
            status="warn" if anomalies else "ok",
            summary=f"{len(anomalies)} anomalies detected",
            anomalies=anomalies,
        )

        # 4. Audit ---------------------------------------------------------
        compliance = self.compliance.evaluate(resources)
        result.compliance = compliance
        result.add_stage(
            "audit",
            status="error" if not compliance.passed else "ok",
            summary=f"{len(compliance.violations)} violations, score {compliance.score}",
            score=compliance.score,
            by_severity=compliance.by_severity(),
        )

        # 5. Remediate -----------------------------------------------------
        planned = self.remediation.plan_remediations(compliance.violations, resources)
        fixed_resources = {r.id: r for r in resources}
        for action, fixed in planned:
            action.rationale = self._rationale(action)
            if auto_remediate:
                self.remediation.apply(action)
                fixed_resources[fixed.id] = fixed
            result.remediations.append(action)

        if auto_remediate and planned:
            # 6. Re-audit to prove the loop actually closed
            post = self.compliance.evaluate(list(fixed_resources.values()))
            result.add_stage(
                "remediate",
                summary=(
                    f"{result.applied_count} fixes applied, "
                    f"score {compliance.score} -> {post.score}"
                ),
                applied=result.applied_count,
                score_before=compliance.score,
                score_after=post.score,
            )
            result.compliance = post
            result.resources = list(fixed_resources.values())
        else:
            result.add_stage(
                "remediate",
                status="warn",
                summary=f"{len(planned)} remediations proposed (dry-run)",
                proposed=len(planned),
            )
        return result

    def _rationale(self, action) -> str | None:
        thought = self.remediator.think(
            f"Violation of policy {action.violation_policy_id} on resource "
            f"{action.resource_id}. Proposed fix: {action.description}. "
            "In one sentence, justify why this is the correct least-privilege remediation."
        )
        return thought
