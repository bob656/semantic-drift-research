def extract_span(text, start, end, strip_result=False):
    if start < 0 or end >= len(text) or start > end:
        return ""
    span = text[start:end + 1]
    if strip_result:
        span = span.strip()
    return span