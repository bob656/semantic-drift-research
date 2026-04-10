def run_checks(candidate):
    results = []

    try:
        value = candidate.extract_span("abcdef", 1, 3)
        results.append(
            {
                "target": "test_end_is_inclusive",
                "status": "pass" if value == "bcd" else "fail",
                "details": f"expected 'bcd', got {value!r}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_end_is_inclusive", "status": "fail", "details": str(exc)})

    try:
        value = candidate.extract_span("abcdef", 5, 1)
        results.append(
            {
                "target": "test_invalid_range_returns_empty",
                "status": "pass" if value == "" else "fail",
                "details": f"expected empty string, got {value!r}",
            }
        )
    except Exception as exc:
        results.append({"target": "test_invalid_range_returns_empty", "status": "fail", "details": str(exc)})

    return results
