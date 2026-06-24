"""The InfraPilot agent crew.

Each agent owns a role, a goal and a set of tools. The native engine drives them
deterministically; the CrewAI engine maps the same roles/goals/tools onto a
CrewAI ``Crew`` so the orchestration layer is swappable.
"""

from infrapilot.agents.auditor import ComplianceAuditor
from infrapilot.agents.base import Agent
from infrapilot.agents.configurator import Configurator
from infrapilot.agents.observer import Observer
from infrapilot.agents.provisioner import Provisioner
from infrapilot.agents.remediator import Remediator

CREW = [Provisioner, Configurator, Observer, ComplianceAuditor, Remediator]

__all__ = [
    "Agent",
    "Provisioner",
    "Configurator",
    "Observer",
    "ComplianceAuditor",
    "Remediator",
    "CREW",
]
