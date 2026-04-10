def run_checks(candidate):
    results = []

    try:
        value = candidate.extract_span("a  b   c", 0, 7, normalize_whitespace=True)
        results.append(
            {
                "target": "normalize_whitespace",
                "status": "pass" if value == "a b c" else "fail",
                "details": f"expected 'a b c', got {value!r}",
            }
        )
    except Exception as exc:
        results.append({"target": "step1_exception", "status": "fail", "details": str(exc)})

    return results
