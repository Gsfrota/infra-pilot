from infrapilot.models import Resource, Severity
from infrapilot.tools.compliance_tool import ComplianceTool

POLICIES = [
    {
        "id": "SEC-001",
        "name": "No SSH open",
        "severity": "critical",
        "resource_type": "security_group",
        "rule": "no_ingress_cidr",
        "params": {"port": 22, "forbidden_cidr": "0.0.0.0/0"},
        "remediation": "restrict_sg_ingress",
    },
    {
        "id": "TAG-001",
        "name": "Owner tag",
        "severity": "medium",
        "resource_type": "*",
        "rule": "required_tag",
        "params": {"tag": "owner"},
        "remediation": "add_tag",
    },
]


def test_detects_open_ssh_and_missing_tag():
    sg = Resource(
        id="web-sg",
        type="security_group",
        attributes={"ingress": [{"port": 22, "cidr": "0.0.0.0/0"}]},
    )
    result = ComplianceTool(POLICIES).evaluate([sg])

    assert result.evaluated == 1
    policy_ids = {v.policy_id for v in result.violations}
    assert policy_ids == {"SEC-001", "TAG-001"}
    # critical sorts before medium
    assert result.violations[0].severity == Severity.CRITICAL


def test_compliant_resource_passes():
    sg = Resource(
        id="web-sg",
        type="security_group",
        attributes={"ingress": [{"port": 443, "cidr": "0.0.0.0/0"}]},
        tags={"owner": "team"},
    )
    result = ComplianceTool(POLICIES).evaluate([sg])
    assert result.passed
    assert result.score == 100.0


def test_unknown_rule_raises():
    bad = [{"id": "X", "name": "x", "severity": "low", "rule": "nope", "params": {}}]
    try:
        ComplianceTool(bad).evaluate([Resource(id="r", type="t")])
    except ValueError as exc:
        assert "unknown rule" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
