# Architecture

InfraPilot is organised around one principle: **the tools are the source of
truth, and everything else is a way to drive them.**

```
              ┌─────────────────────────────────────────────┐
              │                 Drivers                      │
              │   CLI   ·   MCP server   ·   CrewAI crew     │
              └───────────────────┬─────────────────────────┘
                                  │  (all call the same tools)
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
import an engine, so they can be reused by the native loop, the CrewAI crew and
the MCP server alike.

### Executor (`infrapilot/executors.py`)
A thin wrapper over `subprocess`. If the target binary (`terraform`,
`ansible-playbook`) is on `PATH` it runs for real; otherwise it returns a
deterministic *simulated* result flagged with `simulated=True`. This is what
makes the project runnable everywhere without hiding the fact that it simulated.

### Agents (`infrapilot/agents/`)
Plain `role / goal / backstory / tools` definitions. They carry an optional LLM
client for reasoning steps. The same definitions are consumed by both engines.

### Engines (`infrapilot/engines/`)
- **native** — a deterministic loop coordinating the crew and tools. No heavy
  dependencies; this is what CI runs and the tests exercise.
- **crewai** — wraps the tools as CrewAI tools and runs a sequential `Crew`
  with an Anthropic model. Optional extra.

### MCP server (`infrapilot/mcp_server/`)
Publishes the tools over the Model Context Protocol so any MCP client can drive
infrastructure operations conversationally.

## Design decisions

| Decision | Rationale |
| --- | --- |
| Simulation fallback in the executor | Run anywhere (CI, laptop) without cloud creds; never silently pretend a real run happened. |
| Policy-as-code in YAML | Add governance rules without touching Python. |
| LLM strictly optional | Deterministic core stays testable; LLM is an enhancement, not a dependency. |
| One tool layer, many drivers | No logic duplicated across CLI / MCP / CrewAI. |
| Typed `PipelineResult` | Every driver returns the same comparable, serialisable object. |

## Extending

- **New policy:** add an entry to `policies/policies.yaml`. If it needs new
  logic, add a checker to `RULES` in `compliance_tool.py`.
- **New remediation:** add a strategy to `STRATEGIES` in `remediation_tool.py`.
- **New cloud provider:** implement a real backend behind `TerraformTool` /
  `AnsibleTool`; the rest of the loop is unchanged.
