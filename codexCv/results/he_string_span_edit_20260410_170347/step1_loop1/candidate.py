<<STATE_DOCUMENT_JSON>>
{
  "schema_version": "codexCv-state-v1",
  "step_id": 0,
  "loop_id": 0,
  "blueprint": {
    "entities": ["text", "start", "end"],
    "public_api": ["extract_span(text, start, end, normalize_whitespace=False)"],
    "state_transitions": [],
    "invariants": [
      {
        "contract_id": "api_signature",
        "type": "api",
        "description": "The function signature remains unchanged.",
        "rationale": "New formatting behavior should not introduce an API break."
      },
      {
        "contract_id": "inclusive_index_semantics",
        "type": "semantic",
        "description": "The `end` index remains inclusive.",
        "rationale": "Adding convenience behavior should not silently change boundary semantics."
      }
    ]
  },
  "delta