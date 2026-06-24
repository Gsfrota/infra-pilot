"""Project paths and fixture loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Repo root = two levels up from this file (infrapilot/config.py -> repo/)
ROOT = Path(__file__).resolve().parent.parent

INFRA_DIR = ROOT / "infra"
TERRAFORM_DIR = INFRA_DIR / "terraform"
ANSIBLE_DIR = INFRA_DIR / "ansible"
OBSERVABILITY_DIR = INFRA_DIR / "observability"
POLICIES_DIR = ROOT / "policies"
WORK_DIR = ROOT / ".infrapilot"

DESIRED_STATE = INFRA_DIR / "desired_state.yaml"
METRICS_FILE = OBSERVABILITY_DIR / "metrics.json"
POLICIES_FILE = POLICIES_DIR / "policies.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def ensure_workdir() -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    return WORK_DIR
