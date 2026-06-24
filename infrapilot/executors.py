"""Command execution layer.

Every tool runs through a :class:`CommandExecutor`. When the real binary
(``terraform``, ``ansible-playbook``) is available it is invoked for real;
otherwise the executor transparently falls back to a deterministic *simulated*
run so the whole pipeline stays runnable on laptops and in CI without cloud
credentials. The simulation is explicit and labelled — never silent.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class ExecResult:
    command: str
    returncode: int
    stdout: str
    stderr: str = ""
    simulated: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CommandExecutor:
    """Run shell commands with an automatic simulation fallback."""

    def __init__(self, *, force_simulate: bool = False, cwd: str | None = None) -> None:
        self.force_simulate = force_simulate
        self.cwd = cwd

    def available(self, binary: str) -> bool:
        return shutil.which(binary) is not None

    def run(
        self,
        args: list[str],
        *,
        simulate_stdout: str = "",
        cwd: str | None = None,
        timeout: int = 600,
    ) -> ExecResult:
        binary = args[0]
        command = " ".join(args)
        if self.force_simulate or not self.available(binary):
            return ExecResult(
                command=command,
                returncode=0,
                stdout=simulate_stdout or f"[simulated] {command}",
                simulated=True,
            )
        try:
            proc = subprocess.run(  # noqa: S603 - args are constructed by trusted tools
                args,
                cwd=cwd or self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return ExecResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                simulated=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - defensive
            return ExecResult(command=command, returncode=1, stdout="", stderr=str(exc))
