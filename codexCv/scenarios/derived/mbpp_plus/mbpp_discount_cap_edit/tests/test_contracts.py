def run_checks(candidate):
    results = []

    try:
        value = candidate.final_price(100, 75)
        results.append(
            {
                "target": "test_discount_cap",
                "status": "pass" if abs(value - 50.0) < 1e-6 else "fail",
                "details": f"expected 50.0 after cap, got {value}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_discount_cap", "status": "fail", "details": str(exc)})

    try:
        value = candidate.final_price(10, 500)
        results.append(
            {
                "target": "test_nonnegative_total",
                "status": "pass" if value >= 0 else "fail",
                "details": f"expected non-negative value, got {value}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_nonnegative_total", "status": "fail", "details": str(exc)})

    return results
