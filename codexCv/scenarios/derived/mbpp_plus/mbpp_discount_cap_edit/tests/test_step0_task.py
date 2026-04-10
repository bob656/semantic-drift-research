def run_checks(candidate):
    results = []

    try:
        capped = candidate.final_price(100, 80)
        floor_val = candidate.final_price(10, 200)
        results.extend(
            [
                {"target": "discount_cap", "status": "pass" if abs(capped - 50.0) < 1e-6 else "fail", "details": f"expected 50.0, got {capped}"},
                {"target": "nonnegative_floor", "status": "pass" if floor_val >= 0 else "fail", "details": f"expected non-negative price, got {floor_val}"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step0_exception", "status": "fail", "details": str(exc)})

    return results
