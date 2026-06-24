"""Provisioning tool backed by Terraform (with a simulation fallback)."""

from __future__ import annotations

import json

from infrapilot import config
from infrapilot.executors import CommandExecutor, ExecResult
from infrapilot.models import Resource


class TerraformTool:
    """Plan and apply infrastructure declared in ``infra/desired_state.yaml``.

    When the ``terraform`` binary is present the real ``init``/``plan``/``apply``
    cycle runs against ``infra/terraform`` (which uses only the local/null/random
    providers, so no cloud account is required). Otherwise the desired state is
    materialised into ``.infrapilot/state.json`` by the simulator.
    """

    name = "terraform_provision"
    description = "Provision infrastructure from the declarative desired state."

    def __init__(self, executor: CommandExecutor | None = None) -> None:
        self.executor = executor or CommandExecutor()

    def _load_desired(self) -> list[Resource]:
        data = config.load_yaml(config.DESIRED_STATE)
        return [Resource(**r) for r in data.get("resources", [])]

    def plan(self) -> ExecResult:
        return self.executor.run(
            ["terraform", "plan", "-no-color"],
            cwd=str(config.TERRAFORM_DIR),
            simulate_stdout=self._simulated_plan(),
        )

    def apply(self) -> tuple[list[Resource], ExecResult]:
        # Best-effort real init+apply; the simulator ignores the result and
        # materialises desired state so downstream stages always have data.
        self.executor.run(
            ["terraform", "init", "-no-color", "-input=false"],
            cwd=str(config.TERRAFORM_DIR),
            simulate_stdout="[simulated] terraform init",
        )
        result = self.executor.run(
            ["terraform", "apply", "-auto-approve", "-no-color"],
            cwd=str(config.TERRAFORM_DIR),
            simulate_stdout=self._simulated_plan(),
        )
        resources = self._load_desired()
        self._write_state(resources)
        return resources, result

    def _simulated_plan(self) -> str:
        resources = self._load_desired()
        lines = [f"Plan: {len(resources)} to add, 0 to change, 0 to destroy.", ""]
        for r in resources:
            lines.append(f"  + {r.type}.{r.id}")
        return "\n".join(lines)

    def _write_state(self, resources: list[Resource]) -> None:
        workdir = config.ensure_workdir()
        state = {"resources": [r.model_dump() for r in resources]}
        (workdir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
