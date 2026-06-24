"""Pluggable orchestration engines.

``native``  — zero-heavy-dependency multi-agent loop (default; used in CI).
``crewai``  — maps the same crew onto CrewAI (optional extra).
"""

from infrapilot.engines.native import NativeEngine

__all__ = ["NativeEngine", "get_engine"]


def get_engine(name: str):
    if name == "native":
        return NativeEngine
    if name == "crewai":
        from infrapilot.engines.crew import CrewAIEngine  # noqa: PLC0415 - lazy optional dep

        return CrewAIEngine
    raise ValueError(f"unknown engine '{name}' (choose: native, crewai)")
