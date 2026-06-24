from infrapilot.executors import CommandExecutor
from infrapilot.models import Resource, Severity, Violation
from infrapilot.tools.ansible_tool import AnsibleTool
from infrapilot.tools.compliance_tool import ComplianceTool
from infrapilot.tools.remediation_tool import RemediationTool
from infrapilot.tools.terraform_tool import TerraformTool

POLICIES = [
    {
        "id": "SEC-001", "name": "No SSH open", "severity": "critical",
        "resource_type": "security_group", "rule": "no_ingress_cidr",
        "params": {"port": 22, "forbidden_cidr": "0.0.0.0/0"},
        "remediation": "restrict_sg_ingress",
    },
]


def _sim_tool():
    ex = CommandExecutor(force_simulate=True)
    return RemediationTool(TerraformTool(ex), AnsibleTool(ex))


def test_remediation_fixes_make_resource_compliant():
    sg = Resource(
        id="web-sg", type="security_group",
        attributes={"ingress": [{"port": 22, "cidr": "0.0.0.0/0"}]},
        tags={"owner": "team"},
    )
    compliance = ComplianceTool(POLICIES)
    before = compliance.evaluate([sg])
    assert not before.passed

    planned = _sim_tool().plan_remediations(before.violations, [sg])
    assert planned, "expected at least one remediation"
    fixed = [fixed for _, fixed in planned][0]

    after = compliance.evaluate([fixed])
    assert after.passed
    assert after.score > before.score


def test_apply_marks_action_applied():
    action_resource = [
        Violation(
            policy_id="SEC-001", policy_name="No SSH open", severity=Severity.CRITICAL,
            resource_id="web-sg", resource_type="security_group",
            detail="open", remediation="restrict_sg_ingress",
        )
    ]
    sg = Resource(
        id="web-sg", type="security_group",
        attributes={"ingress": [{"port": 22, "cidr": "0.0.0.0/0"}]},
    )
    tool = _sim_tool()
    planned = tool.plan_remediations(action_resource, [sg])
    action = tool.apply(planned[0][0])
    assert action.applied is True
