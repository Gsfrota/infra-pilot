from infrapilot.tools.monitoring_tool import MonitoringTool


def test_detects_high_cpu_and_disk():
    metrics = {
        "targets": [
            {"resource_id": "api-vm", "cpu_pct": 95.0, "status": "up"},
            {"resource_id": "db", "disk_pct": 90.0, "status": "up"},
            {"resource_id": "ok-node", "cpu_pct": 10.0, "status": "up"},
        ]
    }
    anomalies = MonitoringTool().detect_anomalies(metrics)
    flagged = {(a["resource_id"], a["metric"]) for a in anomalies}
    assert ("api-vm", "cpu_pct") in flagged
    assert ("db", "disk_pct") in flagged
    assert all(a["resource_id"] != "ok-node" for a in anomalies)


def test_detects_down_target_as_critical():
    metrics = {"targets": [{"resource_id": "api-vm", "status": "down"}]}
    anomalies = MonitoringTool().detect_anomalies(metrics)
    assert anomalies[0]["severity"] == "critical"
    assert anomalies[0]["metric"] == "availability"


def test_real_fixture_loads():
    # the shipped snapshot must parse and produce at least one anomaly
    assert MonitoringTool().detect_anomalies()
