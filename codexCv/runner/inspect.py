from __future__ import annotations

import argparse
import json

from .catalog import list_scenarios
from .load_scenario import collect_test_targets, load_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect codexCv scenarios")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument(
        "--scenario",
        help="Scenario id relative to codexCv/scenarios, e.g. controlled/order_system_v1",
    )
    args = parser.parse_args()

    if args.list:
        for scenario_id in list_scenarios():
            print(scenario_id)
        return 0

    if args.scenario:
        scenario = load_scenario(args.scenario)
        summary = {
            "scenario_id": scenario["scenario_id"],
            "track": scenario["track"],
            "source": scenario["source"],
            "num_steps": len(scenario["steps"]) + 1,
            "num_contracts": len(scenario["contracts"]),
            "test_targets": collect_test_targets(scenario),
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
