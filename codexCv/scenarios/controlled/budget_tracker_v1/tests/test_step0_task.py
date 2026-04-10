def run_checks(candidate):
    results = []

    try:
        tracker = candidate.BudgetTracker(100.0)
        tracker.add_expense("food", 25.0)
        tracker.add_expense("travel", 15.0)
        spent = tracker.get_total_spent()
        remaining = tracker.get_remaining_budget()
        tracker.close_month()
        rolled_remaining = tracker.get_remaining_budget()

        results.extend(
            [
                {"target": "total_spent", "status": "pass" if abs(spent - 40.0) < 1e-6 else "fail", "details": f"expected 40.0, got {spent}"},
                {"target": "remaining_budget", "status": "pass" if abs(remaining - 60.0) < 1e-6 else "fail", "details": f"expected 60.0, got {remaining}"},
                {"target": "close_month_rollover", "status": "pass" if rolled_remaining >= 60.0 else "fail", "details": f"expected rollover to preserve unused budget, got {rolled_remaining}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step0_exception", "status": "fail", "details": str(exc)})

    return results
