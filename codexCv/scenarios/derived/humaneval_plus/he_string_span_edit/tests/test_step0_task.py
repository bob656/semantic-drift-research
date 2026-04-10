def run_checks(candidate):
    results = []

    try:
        ok = candidate.extract_span("abcdef", 1, 3) == "bcd"
        invalid = candidate.extract_span("abcdef", 5, 1) == ""
        results.extend(
            [
                {"target": "inclusive_extract", "status": "pass" if ok else "fail", "details": "extract_span('abcdef',1,3) should be 'bcd'"},
                {"target": "invalid_range_empty", "status": "pass" if invalid else "fail", "details": "invalid ranges should return empty string"},
            ]
        )
    except Exception as exc:
        results.append({"target": "step0_exception", "status": "fail", "details": str(exc)})

    return results
