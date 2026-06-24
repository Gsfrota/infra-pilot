# Architecture

InfraPilot is organised around one principle: **the tools are the source of
truth, and everything else is a way to drive them.**

```
              ┌─────────────────────────────────────────────┐
              │                 Drivers                      │
              │      CLI        ·        MCP server          │
              └───────────────────┬─────────────────────────┘
                                  │  (both call the same orchestrator + tools)
              ┌───────────────────▼─────────────────────────┐
              │     Orchestrator + agent crew                 │
              │  Provisioner · Configurator · Observer ·      │
              │  Compliance Auditor · Remediator              │
              │     (optional Claude reasoning per agent)     │
              └───────────────────┬─────────────────────────┘
                                  │
              ┌───────────────────▼─────────────────────────┐
              │                  Tools                        │
              │  Terraform · Ansible · Monitoring ·           │
              │  Compliance (policy-as-code) · Remediation    │
              └───────────────────┬─────────────────────────┘
                                  │
              ┌───────────────────▼─────────────────────────┐
              │                Executor                       │
              │  real binary if present, else simulation      │
              └──────────────────────────────────────────────┘
```

## Components

### Tools (`infrapilot/tools/`)
Each tool is a small, testable class with a single responsibility. They never
import the orchestrator, so they are reused by both the CLI loop and the MCP
server.

### Executor (`infrapilot/executors.py`)
A thin wrapper over `subprocess`. If the target binary (`terraform`,
`ansible-playbook`) is on `PATH` it runs for real; otherwise it returns a
deterministic *simulated* result flagged with `simulated=True`. This is what
makes the project runnable everywhere without hiding the fact that it simulated.

### Agents (`infrapilot/agents/`)
Plain `role / goal / backstory / tools` definitions. They carry an optional
Claude client for reasoning steps (anomaly triage, remediation rationale).

### Orchestrator (`infrapilot/engines/native.py`)
A deterministic loop that coordinates the agent crew and their tools through the
full ops cycle. No heavy dependencies, so it runs everywhere — this is what CI
runs and the tests exercise. Each agent optionally calls Claude to reason about
its step; with no API key the loop still completes deterministically.

### MCP server (`infrapilot/mcp_server/`)
Publishes the tools over the Model Context Protocol so any MCP client can drive
infrastructure operations conversationally.

## Design decisions

| Decision | Rationale |
| --- | --- |
| Simulation fallback in the executor | Run anywhere (CI, laptop) without cloud creds; never silently pretend a real run happened. |
| Policy-as-code in YAML | Add governance rules without touching Python. |
| LLM strictly optional | Deterministic core stays testable; LLM is an enhancement, not a dependency. |
| One tool layer, many drivers | No logic duplicated across CLI and MCP server. |
| Typed `PipelineResult` | Every driver returns the same comparable, serialisable object. |

## Extending

- **New policy:** add an entry to `policies/policies.yaml`. If it needs new
  logic, add a checker to `RULES` in `compliance_tool.py`.
- **New remediation:** add a strategy to `STRATEGIES` in `remediation_tool.py`.
- **New cloud provider:** implement a real backend behind `TerraformTool` /
  `AnsibleTool`; the rest of the loop is unchanged.
