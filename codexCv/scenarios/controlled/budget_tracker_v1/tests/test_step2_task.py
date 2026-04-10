def run_checks(candidate):
    results = []

    try:
        tracker = candidate.BudgetTracker(50.0)
        tracker.add_expense("food", 60.0)
        is_over = tracker.is_over_budget()
        alert = tracker.get_alert_message()

        results.extend(
            [
                {"target": "is_over_budget", "status": "pass" if is_over is True else "fail", "details": f"expected True, got {is_over}"},
                {"target": "alert_message", "status": "pass" if isinstance(alert, str) and alert else "fail", "details": f"expected non-empty string, got {alert!r}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step2_exception", "status": "fail", "details": str(exc)})

    return results
