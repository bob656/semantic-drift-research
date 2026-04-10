def run_checks(candidate):
    results = []

    try:
        value = candidate.final_price(100, 20, tax_percent=10)
        results.append(
            {
                "target": "tax_support",
                "status": "pass" if abs(value - 88.0) < 1e-6 else "fail",
                "details": f"expected 88.0, got {value}",
            }
        )
    except Exception as exc:
        results.append({"target": "step1_exception", "status": "fail", "details": str(exc)})

    return results
