Extend `extract_span(text, start, end)` with whitespace normalization.

Requirements:

- Add an optional keyword argument `normalize_whitespace=False`.
- If enabled, collapse multiple spaces in the extracted substring into a single space.
- Keep the original inclusive boundary semantics.
- Existing invalid-range behavior must remain unchanged.

Return complete Python code only.
