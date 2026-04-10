def run_checks(candidate):
    results = []

    try:
        tracker = candidate.BudgetTracker(100.0)
        tracker.add_expense("food", 25.0)
        tracker.close_month()
        remaining = tracker.get_remaining_budget()
        results.append(
            {
                "target": "test_rollover_semantics",
                "status": "pass" if remaining >= 75.0 else "fail",
                "details": f"expected rollover to retain unused budget, got {remaining}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_rollover_semantics", "status": "fail", "details": str(exc)})

    try:
        tracker = candidate.BudgetTracker(50.0)
        tracker.add_expense("food", 80.0)
        remaining = tracker.get_remaining_budget()
        results.append(
            {
                "target": "test_balance_sign_convention",
                "status": "pass" if remaining <= 0 else "fail",
                "details": f"overspent budget should not appear positive, got {remaining}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_balance_sign_convention", "status": "fail", "details": str(exc)})

    return results
