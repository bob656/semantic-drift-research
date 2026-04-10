def extract_span(text, start, end, normalize_whitespace=False):
    if start < 0 or end >= len(text) or start > end:
        return ""
    span = text[start:end + 1]
    if normalize_whitespace:
        span = ' '.join(span.split())
    return span