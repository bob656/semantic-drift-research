from __future__ import annotations

import copy
import json
import ast
from typing import Any, Dict, List


STATE_DOC_SCHEMA_VERSION = "codexCv-state-v1"


STATE_DOC_TEMPLATE: Dict[str, Any] = {
    "schema_version": STATE_DOC_SCHEMA_VERSION,
    "step_id": 0,
    "loop_id": 0,
    "blueprint": {
        "entities": [],
        "public_api": [],
        "state_transitions": [],
        "invariants": [],
    },
    "delta": {
        "changed": [],
        "unchanged": [],
        "removed": [],
    },
    "risks": [],
    "grounding_notes": [],
}


def fresh_state_doc() -> Dict[str, Any]:
    return copy.deepcopy(STATE_DOC_TEMPLATE)


def normalize_state_doc(state_doc: Dict[str, Any], step_id: int, loop_id: int) -> Dict[str, Any]:
    """Coerce partial or malformed state docs into the benchmark schema."""
    normalized = fresh_state_doc()

    if isinstance(state_doc, dict):
        normalized["schema_version"] = state_doc.get("schema_version", STATE_DOC_SCHEMA_VERSION)
        normalized["step_id"] = state_doc.get("step_id", step_id)
        normalized["loop_id"] = state_doc.get("loop_id", loop_id)

        blueprint = state_doc.get("blueprint", {})
        if isinstance(blueprint, dict):
            for key in normalized["blueprint"]:
                value = blueprint.get(key, [])
                normalized["blueprint"][key] = value if isinstance(value, list) else []

        delta = state_doc.get("delta", {})
        if isinstance(delta, dict):
            for key in normalized["delta"]:
                value = delta.get(key, [])
                normalized["delta"][key] = value if isinstance(value, list) else []

        for key in ["risks", "grounding_notes"]:
            value = state_doc.get(key, [])
            normalized[key] = value if isinstance(value, list) else []
    else:
        normalized["step_id"] = step_id
        normalized["loop_id"] = loop_id

    normalized["step_id"] = step_id
    normalized["loop_id"] = loop_id
    normalized["schema_version"] = STATE_DOC_SCHEMA_VERSION
    return normalized


def render_state_doc_markdown(state_doc: Dict[str, Any]) -> str:
    """Render the structured state document into a human-readable markdown file."""
    doc = normalize_state_doc(
        state_doc,
        step_id=state_doc.get("step_id", 0),
        loop_id=state_doc.get("loop_id", 0),
    )

    lines: List[str] = [
        "# State Document",
        "",
        f"- schema_version: `{doc['schema_version']}`",
        f"- step_id: `{doc['step_id']}`",
        f"- loop_id: `{doc['loop_id']}`",
        "",
        "## Thin Blueprint",
        "",
    ]

    for key, title in [
        ("entities", "Entities"),
        ("public_api", "Public API"),
        ("state_transitions", "State Transitions"),
        ("invariants", "Invariants"),
    ]:
        lines.extend([f"### {title}"])
        values = doc["blueprint"].get(key, [])
        if values:
            lines.extend(_render_bullets(values))
        else:
            lines.append("- (none)")
        lines.append("")

    lines.extend(["## Delta", ""])
    for key, title in [
        ("changed", "Changed"),
        ("unchanged", "Unchanged"),
        ("removed", "Removed"),
    ]:
        lines.extend([f"### {title}"])
        values = doc["delta"].get(key, [])
        if values:
            lines.extend(_render_bullets(values))
        else:
            lines.append("- (none)")
        lines.append("")

    lines.extend(["## Risks", ""])
    lines.extend(_render_bullets(doc.get("risks", [])) or ["- (none)"])
    lines.append("")

    lines.extend(["## Grounding Notes", ""])
    lines.extend(_render_bullets(doc.get("grounding_notes", [])) or ["- (none)"])
    lines.append("")

    return "\n".join(lines)


def _render_bullets(values: List[Any]) -> List[str]:
    lines: List[str] = []
    for value in values:
        if isinstance(value, dict):
            lines.append(f"- `{json.dumps(value, ensure_ascii=False, sort_keys=True)}`")
        else:
            lines.append(f"- {value}")
    return lines


def synthesize_state_doc_from_code(
    code: str,
    previous_state_doc: Dict[str, Any],
    contracts: List[Dict[str, Any]],
    step_id: int,
    loop_id: int,
    reason: str,
) -> Dict[str, Any]:
    """
    Build a minimal but human-readable state document from code when the LLM
    omits or corrupts the structured state document.
    """
    doc = fresh_state_doc()
    doc["step_id"] = step_id
    doc["loop_id"] = loop_id

    public_api: List[str] = []
    entities: List[str] = []

    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                entities.append(node.name)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        signature = _function_signature(item, include_self=True)
                        public_api.append(f"{node.name}.{signature}")
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                public_api.append(_function_signature(node, include_self=False))
    except SyntaxError:
        doc["risks"] = [reason, "Code could not be parsed for structured extraction."]
        doc["grounding_notes"] = ["Fallback state document synthesized from invalid code."]
        return doc

    prev = normalize_state_doc(previous_state_doc, step_id=step_id, loop_id=loop_id)
    prev_api = set(prev["blueprint"].get("public_api", []))
    current_api = set(public_api)

    doc["blueprint"]["entities"] = sorted(set(entities))
    doc["blueprint"]["public_api"] = sorted(current_api)
    doc["blueprint"]["state_transitions"] = list(prev["blueprint"].get("state_transitions", []))
    doc["blueprint"]["invariants"] = [contract["description"] for contract in contracts]

    doc["delta"]["changed"] = sorted(current_api - prev_api) or [reason]
    doc["delta"]["unchanged"] = sorted(current_api & prev_api)
    doc["delta"]["removed"] = sorted(prev_api - current_api)
    doc["risks"] = [reason]
    doc["grounding_notes"] = [
        "State document synthesized by harness from AST-visible entities and APIs."
    ]
    return doc


def _function_signature(node: ast.FunctionDef, include_self: bool) -> str:
    arg_names = [arg.arg for arg in node.args.args]
    if not include_self and arg_names and arg_names[0] == "self":
        arg_names = arg_names[1:]
    return f"{node.name}({', '.join(arg_names)})"
