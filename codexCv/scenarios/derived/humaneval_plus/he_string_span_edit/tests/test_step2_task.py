def run_checks(candidate):
    results = []

    try:
        value = candidate.extract_span("  abc  ", 0, 6, strip_result=True)
        results.append(
            {
                "target": "strip_result",
                "status": "pass" if value == "abc" else "fail",
                "details": f"expected 'abc', got {value!r}",
            }
        )
    except Exception as exc:
        results.append({"target": "step2_exception", "status": "fail", "details": str(exc)})

    return results
