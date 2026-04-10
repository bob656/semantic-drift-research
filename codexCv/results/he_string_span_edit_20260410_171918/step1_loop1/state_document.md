# State Document

- schema_version: `codexCv-state-v1`
- step_id: `1`
- loop_id: `1`

## Thin Blueprint

### Entities
- (none)

### Public API
- extract_span(text, start, end)

### State Transitions
- (none)

### Invariants
- extract_span(text, start, end) signature must remain unchanged.
- The `end` index remains inclusive.
- Invalid ranges still return an empty string rather than raising.

## Delta

### Changed
- extract_span(text, start, end)

### Unchanged
- (none)

### Removed
- (none)

## Risks

- (none)

## Grounding Notes

- (none)
