def run_checks(candidate):
    results = []

    try:
        value = candidate.final_price(99.99, 10, tax_percent=7.5, round_to=2)
        results.append(
            {
                "target": "rounded_output",
                "status": "pass" if value == round(value, 2) else "fail",
                "details": f"expected rounded float, got {value}",
            }
        )
    except Exception as exc:
        results.append({"target": "step2_exception", "status": "fail", "details": str(exc)})

    return results
