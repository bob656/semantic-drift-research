from __future__ import annotations

from pathlib import Path
from typing import List


def _scenario_root() -> Path:
    return Path(__file__).resolve().parent.parent / "scenarios"


def list_scenarios() -> List[str]:
    """Return scenario ids as relative paths under `scenarios/`."""
    root = _scenario_root()
    scenario_ids: List[str] = []

    for scenario_json in sorted(root.glob("**/scenario.json")):
        scenario_dir = scenario_json.parent
        scenario_ids.append(str(scenario_dir.relative_to(root)))

    return scenario_ids
