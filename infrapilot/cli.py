"""InfraPilot command-line interface."""

from __future__ import annotations

import typer
from rich.console import Console

from infrapilot import __version__, config
from infrapilot.engines import get_engine
from infrapilot.reporting import render_console, write_artifacts

app = typer.Typer(
    add_completion=False,
    help="Agentic AI for infrastructure operations — provision, monitor, audit, remediate.",
)
console = Console()


def _run(simulate: bool, auto_remediate: bool, artifacts: bool):
    engine = get_engine("native")(simulate=simulate)
    result = engine.run(auto_remediate=auto_remediate)
    render_console(result, console)
    if artifacts:
        paths = write_artifacts(result, config.WORK_DIR / "reports")
        console.print(f"\n[dim]artifacts:[/] {paths['json']}  {paths['markdown']}")
    return result


@app.command()
def run(
    simulate: bool = typer.Option(False, help="Force-simulate terraform/ansible execution."),
    no_remediate: bool = typer.Option(False, help="Audit only; propose fixes without applying."),
    artifacts: bool = typer.Option(True, help="Write JSON/Markdown report artifacts."),
):
    """Run the full ops loop: provision -> configure -> observe -> audit -> remediate."""
    result = _run(simulate, not no_remediate, artifacts)
    # non-zero exit if anything is still non-compliant (useful as a CI gate)
    raise typer.Exit(code=0 if result.compliance.passed else 2)


@app.command()
def audit(
    simulate: bool = typer.Option(False, help="Force-simulate execution."),
):
    """Provision and audit only — never applies remediations (CI compliance gate)."""
    result = _run(simulate, auto_remediate=False, artifacts=False)
    raise typer.Exit(code=0 if result.compliance.passed else 2)


@app.command()
def demo():
    """Self-contained simulated run — no cloud, no API key, no binaries required."""
    _run(simulate=True, auto_remediate=True, artifacts=True)


@app.command()
def version():
    """Print the InfraPilot version."""
    console.print(f"InfraPilot {__version__}")


def main(argv: list[str] | None = None) -> None:
    app()


if __name__ == "__main__":
    app()
