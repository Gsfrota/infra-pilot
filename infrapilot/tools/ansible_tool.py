"""Configuration-management tool backed by Ansible (simulation fallback)."""

from __future__ import annotations

from infrapilot import config
from infrapilot.executors import CommandExecutor, ExecResult


class AnsibleTool:
    """Apply configuration via an Ansible playbook against localhost.

    Used both for initial configuration and as a remediation backend (e.g.
    restart a drifted service, harden an OS setting).
    """

    name = "ansible_configure"
    description = "Apply configuration management with Ansible."

    def __init__(self, executor: CommandExecutor | None = None) -> None:
        self.executor = executor or CommandExecutor()

    def run_playbook(self, playbook: str = "site.yml", tags: list[str] | None = None) -> ExecResult:
        args = [
            "ansible-playbook",
            "-i",
            "inventory.ini",
            playbook,
        ]
        if tags:
            args += ["--tags", ",".join(tags)]
        return self.executor.run(
            args,
            cwd=str(config.ANSIBLE_DIR),
            simulate_stdout=(
                "PLAY RECAP\n"
                "localhost : ok=4 changed=2 unreachable=0 failed=0 skipped=0\n"
                f"[simulated] applied {playbook}"
                + (f" (tags={tags})" if tags else "")
            ),
        )
