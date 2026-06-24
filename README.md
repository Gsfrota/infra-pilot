# InfraPilot 🛰️

**Agentic AI for infrastructure operations.** A multi-agent system that
**provisions**, **monitors**, **validates compliance** and **auto-remediates**
cloud, network and security infrastructure — built on **Python**, **MCP**,
**Anthropic Claude**, **Terraform** and **Ansible**.

[![CI](https://github.com/Gsfrota/infra-pilot/actions/workflows/ci.yml/badge.svg)](https://github.com/Gsfrota/infra-pilot/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![IaC](https://img.shields.io/badge/IaC-Terraform%20%7C%20Ansible-7B42BC)

> InfraPilot closes the full ops loop end-to-end:
> **provision → configure → observe → audit → remediate → re-audit**,
> coordinated by a crew of specialised AI agents — and it runs out of the box
> with **no cloud account, no API key and no Terraform/Ansible binaries
> required** (it transparently simulates execution when a binary is absent).

---

## Why it exists

Most "AI for DevOps" demos stop at a chatbot that writes a Terraform snippet.
InfraPilot models the *operational loop* an automation engineer actually owns:
turning declarative intent into running infrastructure, watching it, proving it
meets security/governance policy, and **fixing drift automatically through
code** — with every action typed, reported and auditable.

## Architecture

Two ways to drive it (CLI or MCP) feed **one orchestrator**. The orchestrator
runs a crew of five agents in sequence; each agent owns exactly one tool, and
every tool runs through a single executor that either calls the real binary or
falls back to a labelled simulation. Claude is an optional reasoning layer wired
into the agents — never a hard dependency.

```mermaid
flowchart TB
    CLI["CLI · infrapilot run"] --> ORCH
    MCPC["MCP client · Claude Desktop / Code"] --> MCPS["MCP server"] --> ORCH

    subgraph ORCH["Orchestrator — sequential ops loop"]
        direction LR
        P[Provisioner] --> C[Configurator] --> O[Observer] --> A[Compliance Auditor] --> R[Remediator]
        R -. re-audit .-> A
    end

    CLAUDE["Anthropic Claude · optional<br/>anomaly triage · remediation rationale"] -. reasoning .-> ORCH

    P --> TF[Terraform tool]
    C --> AN[Ansible tool]
    O --> MON[Monitoring tool]
    A --> POL[Policy-as-code engine]
    R --> REM[Remediation strategies]

    TF --> EX
    AN --> EX
    MON --> EX
    POL --> EX
    REM --> EX
    EX["Executor — real binary if present, else simulated"] --> STATE[("Infra state · Terraform / Ansible")]
```

- **One orchestrator, one job each.** A dependency-free sequential loop
  coordinates the five agents; the whole thing runs in CI and is what the tests
  exercise — no heavyweight agent framework to install or mock.
- **Tools are the source of truth.** Terraform, Ansible, monitoring, policy and
  remediation logic live in `infrapilot/tools/`, shared by both the CLI loop and
  the MCP server — one implementation, two ways to drive it.
- **MCP-native.** `infrapilot/mcp_server/` exposes the tools over the **Model
  Context Protocol**, so Claude Desktop / Claude Code / any MCP client can run
  infra operations through natural language.
- **Claude optional.** With `ANTHROPIC_API_KEY` set, each agent calls Claude to
  triage anomalies and justify remediations. Without it, the loop still completes
  deterministically.

## Quickstart

```bash
git clone https://github.com/Gsfrota/infra-pilot && cd infra-pilot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

infrapilot demo          # fully simulated end-to-end run — no creds needed
```

Example output (abridged):

```
╭──────────────────────── InfraPilot run ────────────────────────╮
│ engine=native  llm=off  compliance score=100.0/100             │
╰────────────────────────────────────────────────────────────────╯
 provision   ok     4 resources provisioned (simulated)
 configure   ok     configuration applied (simulated)
 observe     warn   3 anomalies detected
 audit       error  3 violations, score 43.8
 remediate   ok     3 fixes applied, score 43.8 -> 100.0
```

### Commands

| Command | What it does |
| --- | --- |
| `infrapilot demo` | Self-contained simulated run (no cloud/API key/binaries). |
| `infrapilot run` | Full loop; uses real `terraform`/`ansible` if installed. |
| `infrapilot run --no-remediate` | Audit + propose fixes without applying. |
| `infrapilot audit` | Compliance gate — exits non-zero on any violation (great in CI). |

### Use it from Claude (MCP)

```bash
pip install -e ".[mcp]"
infrapilot-mcp            # serves the tools over MCP (stdio)
```

```jsonc
// claude_desktop_config.json
{
  "mcpServers": {
    "infrapilot": { "command": "infrapilot-mcp" }
  }
}
```

Then ask Claude: *"Provision the infra, audit it for security issues, and
remediate anything critical."*

## How the loop works

1. **Provision** — `TerraformTool` applies `infra/desired_state.yaml` (real
   `terraform apply` against the local/null/random providers when the binary is
   present; simulated otherwise).
2. **Configure** — `AnsibleTool` converges host configuration via a playbook.
3. **Observe** — `MonitoringTool` ingests a Prometheus-style telemetry snapshot
   and triages anomalies against thresholds.
4. **Audit** — the **policy-as-code** engine evaluates every resource against
   `policies/policies.yaml`; new governance rules are added in YAML, not code.
5. **Remediate** — `RemediationTool` maps each violation to a least-privilege
   fix and applies it through the right IaC backend (Terraform or Ansible).
6. **Re-audit** — the loop re-scores compliance to prove the drift is closed.

## Policy-as-code

```yaml
- id: SEC-001
  name: "No SSH open to the internet"
  severity: critical
  resource_type: security_group
  rule: no_ingress_cidr
  params: { port: 22, forbidden_cidr: "0.0.0.0/0" }
  remediation: restrict_sg_ingress
```

Built-in rules: `required_tag`, `no_ingress_cidr`, `attribute_equals`,
`attribute_max`. Built-in remediations: `add_tag`, `restrict_sg_ingress`,
`enable_encryption`, `restart_service`.

## Project layout

```
infrapilot/
├── agents/        # role/goal/backstory crew
├── engines/       # the sequential orchestrator (native.py)
├── tools/         # terraform · ansible · monitoring · compliance · remediation
├── mcp_server/    # MCP server exposing the tools
├── llm.py         # optional Anthropic Claude reasoning layer
├── reporting.py   # rich console + JSON/Markdown artifacts
└── cli.py         # typer CLI
infra/             # terraform/, ansible/, observability/, desired_state.yaml
policies/          # policy-as-code
tests/             # pytest suite (engine, compliance, monitoring, remediation)
```

## Development

```bash
pip install -e ".[dev]"
ruff check .          # lint
pytest                # tests
infrapilot demo       # smoke test the full loop
```

CI (GitHub Actions) runs ruff + pytest on 3.10/3.11/3.12 and additionally
installs **real Terraform and Ansible** to `validate`/`lint` the IaC.

## Roadmap

- [ ] Real cloud providers behind a feature flag (AWS/GCP modules)
- [ ] Parallel agent execution where the loop allows it
- [ ] Drift detection on a schedule (cron / GitHub Actions)
- [ ] OPA/Rego policy backend option

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Guilherme Frota Souza](https://github.com/Gsfrota) — Infrastructure & Automation Engineer.
