from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


class ScenarioValidationError(ValueError):
    """Raised when a scenario is structurally invalid."""


def _scenario_root() -> Path:
    return Path(__file__).resolve().parent.parent / "scenarios"


def _ensure_keys(obj: Dict[str, Any], keys: Iterable[str], where: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise ScenarioValidationError(
            f"{where} is missing required keys: {', '.join(missing)}"
        )


def validate_scenario(data: Dict[str, Any]) -> None:
    """Validate the minimal scenario contract without external deps."""
    _ensure_keys(
        data,
        [
            "scenario_id",
            "track",
            "source",
            "language",
            "description",
            "step0",
            "steps",
            "contracts",
            "evaluation",
        ],
        "scenario",
    )

    if data["track"] not in {"controlled", "derived"}:
        raise ScenarioValidationError("track must be 'controlled' or 'derived'")

    if not isinstance(data["steps"], list) or not data["steps"]:
        raise ScenarioValidationError("steps must be a non-empty list")

    if not isinstance(data["contracts"], list) or not data["contracts"]:
        raise ScenarioValidationError("contracts must be a non-empty list")

    _ensure_keys(data["step0"], ["prompt_file", "task_tests"], "step0")

    for index, step in enumerate(data["steps"], start=1):
        _ensure_keys(
            step,
            ["step_id", "prompt_file", "task_tests", "contracts_checked"],
            f"steps[{index}]",
        )
        if step["step_id"] != index:
            raise ScenarioValidationError(
                f"steps[{index}] has step_id={step['step_id']} but expected {index}"
            )

    seen_contracts = set()
    for index, contract in enumerate(data["contracts"], start=1):
        _ensure_keys(
            contract,
            [
                "contract_id",
                "type",
                "description",
                "rationale",
                "check_type",
                "check_target",
            ],
            f"contracts[{index}]",
        )
        contract_id = contract["contract_id"]
        if contract_id in seen_contracts:
            raise ScenarioValidationError(f"duplicate contract_id: {contract_id}")
        seen_contracts.add(contract_id)

    for index, step in enumerate(data["steps"], start=1):
        unknown = sorted(set(step["contracts_checked"]) - seen_contracts)
        if unknown:
            raise ScenarioValidationError(
                f"steps[{index}] references unknown contracts: {', '.join(unknown)}"
            )

    _ensure_keys(
        data["evaluation"],
        ["task_metric", "contract_metric", "primary_report"],
        "evaluation",
    )


def load_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Load a scenario by path-like id, such as `controlled/order_system_v1`.
    """
    path = _scenario_root() / scenario_id / "scenario.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {scenario_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    validate_scenario(data)
    data["_scenario_dir"] = str(path.parent)
    return data


def load_prompt(scenario_id: str, prompt_file: str) -> str:
    """Load a prompt file relative to its scenario directory."""
    scenario = load_scenario(scenario_id)
    scenario_dir = Path(scenario["_scenario_dir"])
    path = scenario_dir / prompt_file
    return path.read_text(encoding="utf-8")


def collect_test_targets(scenario: Dict[str, Any]) -> Dict[str, List[str]]:
    """Return grouped task and contract targets for reporting or execution."""
    task_tests = list(scenario["step0"]["task_tests"])
    for step in scenario["steps"]:
        task_tests.extend(step["task_tests"])

    contract_tests = [contract["check_target"] for contract in scenario["contracts"]]
    return {
        "task_tests": task_tests,
        "contract_tests": contract_tests,
    }
