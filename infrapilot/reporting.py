"""Render a PipelineResult to the console and to artifact files."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from infrapilot.models import PipelineResult

_STATUS_STYLE = {"ok": "green", "warn": "yellow", "error": "red", "skipped": "dim"}


def render_console(result: PipelineResult, console: Console | None = None) -> None:
    console = console or Console()

    header = (
        f"engine=[bold]{result.engine}[/]  "
        f"llm=[bold]{'on' if result.llm_enabled else 'off'}[/]  "
        f"compliance score=[bold]{result.compliance.score}[/]/100"
    )
    console.print(Panel(header, title="InfraPilot run", border_style="cyan"))

    stages = Table(title="Pipeline stages", show_lines=False, expand=True)
    stages.add_column("stage", style="bold")
    stages.add_column("status")
    stages.add_column("summary")
    for stage in result.stages:
        style = _STATUS_STYLE.get(stage.status, "white")
        stages.add_row(stage.name, f"[{style}]{stage.status}[/]", stage.summary)
    console.print(stages)

    if result.compliance.violations:
        viol = Table(title="Compliance violations", expand=True)
        viol.add_column("severity")
        viol.add_column("policy")
        viol.add_column("resource")
        viol.add_column("detail")
        for v in result.compliance.violations:
            style = "red" if v.severity.value in ("critical", "high") else "yellow"
            viol.add_row(
                f"[{style}]{v.severity.value}[/]",
                f"{v.policy_id} {v.policy_name}",
                v.resource_id,
                v.detail,
            )
        console.print(viol)

    if result.remediations:
        rem = Table(title="Remediations", expand=True)
        rem.add_column("applied")
        rem.add_column("backend")
        rem.add_column("resource")
        rem.add_column("action")
        for r in result.remediations:
            mark = "[green]✓[/]" if r.applied else "[yellow]proposed[/]"
            rem.add_row(mark, r.backend, r.resource_id, r.description)
        console.print(rem)


def to_markdown(result: PipelineResult) -> str:
    lines = [
        "# InfraPilot run report",
        "",
        f"- **Engine:** {result.engine}",
        f"- **LLM reasoning:** {'enabled' if result.llm_enabled else 'disabled'}",
        f"- **Compliance score:** {result.compliance.score}/100",
        f"- **Remediations applied:** {result.applied_count}",
        "",
        "## Stages",
        "",
        "| Stage | Status | Summary |",
        "| --- | --- | --- |",
    ]
    lines += [f"| {s.name} | {s.status} | {s.summary} |" for s in result.stages]
    if result.compliance.violations:
        lines += [
            "",
            "## Violations",
            "",
            "| Severity | Policy | Resource | Detail |",
            "| --- | --- | --- | --- |",
        ]
        lines += [
            f"| {v.severity.value} | {v.policy_id} {v.policy_name} | {v.resource_id} | {v.detail} |"
            for v in result.compliance.violations
        ]
    return "\n".join(lines) + "\n"


def write_artifacts(result: PipelineResult, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(result.model_dump(), indent=2, default=str), encoding="utf-8")
    md_path.write_text(to_markdown(result), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
