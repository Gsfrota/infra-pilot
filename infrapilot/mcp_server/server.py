"""Model Context Protocol (MCP) server for InfraPilot.

Exposes InfraPilot's infrastructure tools over MCP so any MCP-capable client
(Claude Desktop, Claude Code, IDEs) can provision, monitor, audit and remediate
infrastructure through natural language.

Run with::

    python -m infrapilot.mcp_server.server      # stdio transport

Requires the ``mcp`` extra: ``pip install 'infra-pilot[mcp]'``.
"""

from __future__ import annotations

import json

from infrapilot.tools import (
    AnsibleTool,
    ComplianceTool,
    MonitoringTool,
    RemediationTool,
    TerraformTool,
)


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "MCP server requires the 'mcp' extra. Install with: pip install 'infra-pilot[mcp]'"
        ) from exc

    mcp = FastMCP("InfraPilot")
    terraform = TerraformTool()
    ansible = AnsibleTool()
    monitoring = MonitoringTool()
    compliance = ComplianceTool()
    remediation = RemediationTool(terraform, ansible)

    @mcp.tool()
    def terraform_provision() -> str:
        """Provision the declared desired-state infrastructure with Terraform."""
        resources, res = terraform.apply()
        return json.dumps(
            {"resources": [r.model_dump() for r in resources], "simulated": res.simulated}
        )

    @mcp.tool()
    def ansible_configure(playbook: str = "site.yml") -> str:
        """Apply configuration management to hosts with an Ansible playbook."""
        res = ansible.run_playbook(playbook)
        return json.dumps({"stdout": res.stdout, "simulated": res.simulated})

    @mcp.tool()
    def monitoring_query() -> str:
        """Query telemetry and return detected infrastructure anomalies."""
        return json.dumps(monitoring.detect_anomalies())

    @mcp.tool()
    def compliance_audit() -> str:
        """Validate provisioned resources against policy-as-code and list violations."""
        resources, _ = terraform.apply()
        return compliance.evaluate(resources).model_dump_json()

    @mcp.tool()
    def remediate() -> str:
        """Audit, then automatically remediate every fixable compliance violation."""
        resources, _ = terraform.apply()
        result = compliance.evaluate(resources)
        planned = remediation.plan_remediations(result.violations, resources)
        applied = [remediation.apply(action).model_dump() for action, _ in planned]
        return json.dumps({"applied": applied})

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
