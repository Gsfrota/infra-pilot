"""Typed domain models shared across tools, agents and engines."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def weight(self) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}[self.value]


class Resource(BaseModel):
    """A piece of infrastructure under management (cloud, network or security)."""

    id: str
    type: str
    provider: str = "demo"
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)

    def with_tag(self, key: str, value: str) -> Resource:
        new = self.model_copy(deep=True)
        new.tags[key] = value
        return new


class Violation(BaseModel):
    """A single policy violation found on a resource."""

    policy_id: str
    policy_name: str
    severity: Severity
    resource_id: str
    resource_type: str
    detail: str
    remediation: str | None = None


class ComplianceResult(BaseModel):
    """Outcome of a compliance audit over a set of resources."""

    evaluated: int = 0
    violations: list[Violation] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations

    @property
    def score(self) -> float:
        """Compliance score in [0, 100], weighted by severity."""
        if self.evaluated == 0:
            return 100.0
        penalty = sum(v.severity.weight for v in self.violations)
        # cap penalty so a single critical never drops below 0
        max_penalty = self.evaluated * Severity.CRITICAL.weight
        return round(max(0.0, 100.0 * (1 - penalty / max_penalty)), 1)

    def by_severity(self) -> dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for v in self.violations:
            counts[v.severity.value] += 1
        return counts


class RemediationAction(BaseModel):
    """A concrete fix the system proposes (and optionally applies)."""

    violation_policy_id: str
    resource_id: str
    description: str
    strategy: str
    backend: str = "terraform"  # terraform | ansible | api
    applied: bool = False
    rationale: str | None = None  # filled by the LLM when reasoning is enabled


class StageReport(BaseModel):
    name: str
    status: str = "ok"  # ok | warn | error | skipped
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    """End-to-end result of an InfraPilot run."""

    engine: str
    llm_enabled: bool = False
    stages: list[StageReport] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)
    compliance: ComplianceResult = Field(default_factory=ComplianceResult)
    remediations: list[RemediationAction] = Field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return sum(1 for r in self.remediations if r.applied)

    def add_stage(
        self, name: str, status: str = "ok", summary: str = "", **details: Any
    ) -> StageReport:
        report = StageReport(name=name, status=status, summary=summary, details=details)
        self.stages.append(report)
        return report
