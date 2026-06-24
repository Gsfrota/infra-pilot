"""Orchestration engine.

``native`` — a lightweight, dependency-free multi-agent orchestrator that drives
the full ops loop. It coordinates the agent crew and their tools, and uses an
optional Anthropic Claude reasoning layer when an API key is available.
"""

from infrapilot.engines.native import NativeEngine

__all__ = ["NativeEngine", "get_engine"]


def get_engine(name: str):
    if name == "native":
        return NativeEngine
    raise ValueError(f"unknown engine '{name}' (available: native)")
