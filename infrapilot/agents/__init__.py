"""The InfraPilot agent crew.

Each agent owns a role, a goal and a set of tools. The orchestrator drives them
in sequence through the ops loop, and each agent can call the optional Claude
reasoning layer to triage findings and justify decisions.
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
