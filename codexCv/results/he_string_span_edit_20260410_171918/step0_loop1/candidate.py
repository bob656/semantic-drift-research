def extract_span(text, start, end):
    if start < 0 or end >= len(text) or start > end:
        return ""
    return text[start:end + 1]