def run_checks(candidate):
    results = []

    try:
        tracker = candidate.BudgetTracker(100.0)
        tracker.add_expense("food", 25.0)
        report = tracker.export_monthly_report()
        results.extend(
            [
                {"target": "export_report_dict", "status": "pass" if isinstance(report, dict) else "fail", "details": f"expected dict, got {type(report).__name__}"},
                {"target": "export_report_has_spent", "status": "pass" if "total_spent" in report else "fail", "details": f"keys: {sorted(report.keys()) if isinstance(report, dict) else 'n/a'}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step3_exception", "status": "fail", "details": str(exc)})

    return results
