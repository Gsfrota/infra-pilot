"""Observability tool — pulls telemetry and triages anomalies."""

from __future__ import annotations

import json
from typing import Any

from infrapilot import config


class MonitoringTool:
    """Read telemetry (Prometheus-style metric snapshot) and flag anomalies.

    In production this would query a Prometheus/Datadog API; here it reads a
    metrics snapshot from ``infra/observability/metrics.json`` and applies
    threshold rules to surface actionable health issues.
    """

    name = "monitoring_query"
    description = "Query telemetry and detect infrastructure health anomalies."

    THRESHOLDS = {
        "cpu_pct": 85.0,
        "memory_pct": 90.0,
        "disk_pct": 85.0,
        "error_rate": 0.05,
    }

    def query(self) -> dict[str, Any]:
        with config.METRICS_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def detect_anomalies(self, metrics: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        metrics = metrics or self.query()
        anomalies: list[dict[str, Any]] = []
        for target in metrics.get("targets", []):
            for metric, threshold in self.THRESHOLDS.items():
                value = target.get(metric)
                if value is None:
                    continue
                if value > threshold:
                    anomalies.append(
                        {
                            "resource_id": target["resource_id"],
                            "metric": metric,
                            "value": value,
                            "threshold": threshold,
                            "severity": "high" if value > threshold * 1.1 else "medium",
                        }
                    )
            if target.get("status") == "down":
                anomalies.append(
                    {
                        "resource_id": target["resource_id"],
                        "metric": "availability",
                        "value": "down",
                        "threshold": "up",
                        "severity": "critical",
                    }
                )
        return anomalies
