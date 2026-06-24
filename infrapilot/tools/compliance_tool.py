"""Policy-as-code compliance engine.

Evaluates resources against a declarative policy set (``policies/policies.yaml``).
Each policy names a ``rule`` resolved here to a checker function, so new
governance rules are added in YAML without touching agent code.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from infrapilot import config
from infrapilot.models import ComplianceResult, Resource, Severity, Violation

# A rule returns an error message when the resource is non-compliant, else None.
RuleFn = Callable[[Resource, dict[str, Any]], str | None]


def _rule_required_tag(resource: Resource, params: dict[str, Any]) -> str | None:
    tag = params["tag"]
    if tag not in resource.tags or not resource.tags[tag]:
        return f"missing required tag '{tag}'"
    return None


def _rule_no_ingress_cidr(resource: Resource, params: dict[str, Any]) -> str | None:
    port = params["port"]
    forbidden = params["forbidden_cidr"]
    for rule in resource.attributes.get("ingress", []):
        if rule.get("port") == port and rule.get("cidr") == forbidden:
            return f"ingress on port {port} open to {forbidden}"
    return None


def _rule_attribute_equals(resource: Resource, params: dict[str, Any]) -> str | None:
    attr = params["attribute"]
    expected = params["value"]
    actual = resource.attributes.get(attr)
    if actual != expected:
        return f"attribute '{attr}' is {actual!r}, expected {expected!r}"
    return None


def _rule_attribute_max(resource: Resource, params: dict[str, Any]) -> str | None:
    attr = params["attribute"]
    maximum = params["max"]
    actual = resource.attributes.get(attr)
    if actual is not None and actual > maximum:
        return f"attribute '{attr}' is {actual}, exceeds max {maximum}"
    return None


RULES: dict[str, RuleFn] = {
    "required_tag": _rule_required_tag,
    "no_ingress_cidr": _rule_no_ingress_cidr,
    "attribute_equals": _rule_attribute_equals,
    "attribute_max": _rule_attribute_max,
}


class ComplianceTool:
    name = "compliance_audit"
    description = "Validate resources against policy-as-code and report violations."

    def __init__(self, policies: list[dict[str, Any]] | None = None) -> None:
        self.policies = policies if policies is not None else self._load_policies()

    @staticmethod
    def _load_policies() -> list[dict[str, Any]]:
        return config.load_yaml(config.POLICIES_FILE).get("policies", [])

    def _applies(self, policy: dict[str, Any], resource: Resource) -> bool:
        target = policy.get("resource_type", "*")
        return target in ("*", resource.type)

    def evaluate(self, resources: list[Resource]) -> ComplianceResult:
        result = ComplianceResult(evaluated=len(resources))
        for resource in resources:
            for policy in self.policies:
                if not self._applies(policy, resource):
                    continue
                rule_fn = RULES.get(policy["rule"])
                if rule_fn is None:
                    raise ValueError(f"unknown rule '{policy['rule']}' in policy {policy['id']}")
                detail = rule_fn(resource, policy.get("params", {}))
                if detail:
                    result.violations.append(
                        Violation(
                            policy_id=policy["id"],
                            policy_name=policy["name"],
                            severity=Severity(policy["severity"]),
                            resource_id=resource.id,
                            resource_type=resource.type,
                            detail=detail,
                            remediation=policy.get("remediation"),
                        )
                    )
        # surface the most severe violations first
        result.violations.sort(key=lambda v: v.severity.weight, reverse=True)
        return result
