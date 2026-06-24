"""Remediation tool — turns violations into concrete, applied fixes."""

from __future__ import annotations

from collections.abc import Callable

from infrapilot.models import RemediationAction, Resource, Violation
from infrapilot.tools.ansible_tool import AnsibleTool
from infrapilot.tools.terraform_tool import TerraformTool

# A strategy maps a violation+resource to (new_resource, human description, backend).
StrategyFn = Callable[[Violation, Resource], tuple[Resource, str, str]]


def _add_owner_tag(violation: Violation, resource: Resource) -> tuple[Resource, str, str]:
    fixed = resource.with_tag("owner", "platform-team")
    return fixed, "add 'owner' tag via Terraform default_tags", "terraform"


def _restrict_sg_ingress(violation: Violation, resource: Resource) -> tuple[Resource, str, str]:
    fixed = resource.model_copy(deep=True)
    ingress = fixed.attributes.get("ingress", [])
    for rule in ingress:
        if rule.get("port") == 22 and rule.get("cidr") == "0.0.0.0/0":
            rule["cidr"] = "10.0.0.0/8"  # restrict SSH to the internal VPC range
    return fixed, "restrict SSH ingress from 0.0.0.0/0 to 10.0.0.0/8", "terraform"


def _enable_encryption(violation: Violation, resource: Resource) -> tuple[Resource, str, str]:
    fixed = resource.model_copy(deep=True)
    fixed.attributes["encrypted"] = True
    return fixed, "enable at-rest encryption", "terraform"


def _restart_service(violation: Violation, resource: Resource) -> tuple[Resource, str, str]:
    return resource, "restart unhealthy service via Ansible handler", "ansible"


STRATEGIES: dict[str, StrategyFn] = {
    "add_tag": _add_owner_tag,
    "restrict_sg_ingress": _restrict_sg_ingress,
    "enable_encryption": _enable_encryption,
    "restart_service": _restart_service,
}


class RemediationTool:
    name = "remediate"
    description = "Generate and apply remediations for compliance violations."

    def __init__(
        self,
        terraform: TerraformTool | None = None,
        ansible: AnsibleTool | None = None,
    ) -> None:
        self.terraform = terraform or TerraformTool()
        self.ansible = ansible or AnsibleTool()

    def plan_remediations(
        self, violations: list[Violation], resources: list[Resource]
    ) -> list[tuple[RemediationAction, Resource]]:
        """Build remediation actions plus the post-fix resource for each violation.

        Fixes are accumulated per resource: when a resource has several
        violations, each strategy operates on the already-corrected version so
        the final snapshot satisfies *all* of them (not just the last one).
        """
        working = {r.id: r for r in resources}
        planned: list[tuple[RemediationAction, Resource]] = []
        for v in violations:
            if not v.remediation or v.remediation not in STRATEGIES:
                continue
            resource = working.get(v.resource_id)
            if resource is None:
                continue
            fixed, description, backend = STRATEGIES[v.remediation](v, resource)
            working[v.resource_id] = fixed  # accumulate for any later violation
            action = RemediationAction(
                violation_policy_id=v.policy_id,
                resource_id=v.resource_id,
                description=description,
                strategy=v.remediation,
                backend=backend,
            )
            planned.append((action, fixed))
        return planned

    def apply(self, action: RemediationAction) -> RemediationAction:
        """Execute the fix through the appropriate IaC backend."""
        if action.backend == "ansible":
            self.ansible.run_playbook(tags=[action.strategy])
        else:
            # Terraform path: re-applying converges the (now-corrected) desired state.
            self.terraform.apply()
        action.applied = True
        return action
