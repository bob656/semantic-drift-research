def run_checks(candidate):
    results = []

    try:
        tracker = candidate.BudgetTracker(100.0)
        tracker.add_expense("food", 20.0)
        tracker.add_expense("food", 5.0)
        tracker.add_expense("travel", 10.0)
        summary = tracker.get_category_summary()

        food_total = summary.get("food")
        travel_total = summary.get("travel")
        results.extend(
            [
                {"target": "category_summary_food", "status": "pass" if abs(food_total - 25.0) < 1e-6 else "fail", "details": f"expected 25.0, got {food_total}"},
                {"target": "category_summary_travel", "status": "pass" if abs(travel_total - 10.0) < 1e-6 else "fail", "details": f"expected 10.0, got {travel_total}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step1_exception", "status": "fail", "details": str(exc)})

    return results
