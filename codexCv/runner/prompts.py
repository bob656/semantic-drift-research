from __future__ import annotations

import json
from textwrap import dedent
from typing import Any, Dict, List

from .state_doc import STATE_DOC_TEMPLATE


CODE_GENERATOR_SYSTEM_PROMPT = dedent(
    """
    You are a Python code-editing agent in a semantic drift benchmark.

    Your job is to implement the current modification request while preserving
    previously established contracts that are still valid.

    Rules:
    - Do not break public APIs unless the request explicitly requires it.
    - Do not change existing semantics that are unrelated to the current edit.
    - Return complete Python code only.
    - Do not include explanations before or after the code.

    Output format:
    ```python
    # full code
    ```
    """
).strip()

STATE_DOC_UPDATER_SYSTEM_PROMPT = dedent(
    """
    You are a state-document updater for a semantic drift benchmark.

    Your job is to summarize the current code truthfully using the exact state
    document schema. Keep entries terse. Do not include prose outside JSON.

    Rules:
    - Record only facts that are true in the code now.
    - `blueprint` should contain the stable thin blueprint.
    - `delta.changed` should list only facts changed in this step.
    - `delta.unchanged` should list only important preserved facts.
    - `delta.removed` should list facts no longer true.
    - `risks` should list only current grounded risks.
    - `grounding_notes` should be short and factual.

    Return JSON only.
    """
).strip()


EVALUATOR_SYSTEM_PROMPT = dedent(
    """
    You are the evaluator for a semantic drift benchmark.

    Your role is not to praise. Your role is to find mismatches, regressions,
    stale state documentation, broken contracts, and ungrounded claims.

    Evaluation priorities:
    1. Does the code satisfy the current modification request?
    2. Does the state document match the code exactly?
    3. Are preserved contracts still valid?
    4. Does the code introduce unrelated regressions?

    Strict rules:
    - Do not compliment the output.
    - Do not speculate beyond the provided inputs.
    - If evidence is insufficient, mark it as unknown.
    - If the state document claims facts not supported by code or checks,
      treat that as semantic drift.
    - Use the automated signals as hard evidence.

    Return JSON only:
    {
      "task_success": 0,
      "state_alignment": 0,
      "contract_preservation": 0,
      "severity": "pass|warn|fail|critical",
      "drift_detected": true,
      "findings": [
        {
          "type": "state_mismatch|contract_break|task_failure|code_smell|unknown",
          "severity": "low|medium|high|critical",
          "location": "state_doc|code|api|logic|tests|unknown",
          "message": "specific issue",
          "evidence": "brief evidence"
        }
      ],
      "repair_priority": [
        "most important repair action"
      ],
      "summary": "one-line conclusion"
    }
    """
).strip()


CODE_REFINER_SYSTEM_PROMPT = dedent(
    """
    You are the repair agent for a semantic drift benchmark.

    Your job is to repair the code using evaluator findings without introducing
    new regressions.

    Rules:
    - Preserve existing valid behavior.
    - Fix the highest-severity issues first.
    - Return complete Python code only.

    Output format:
    ```python
    # full code
    ```
    """
).strip()


SYNTAX_FIXER_SYSTEM_PROMPT = dedent(
    """
    You repair Python syntax errors.

    Rules:
    - Fix syntax only.
    - Preserve the intended behavior as much as possible.
    - Return complete Python code only.
    - Do not include explanations.
    """
).strip()


JSON_REPAIR_SYSTEM_PROMPT = dedent(
    """
    You repair malformed evaluator JSON.

    Rules:
    - Return one valid JSON object only.
    - Preserve the original meaning.
    - Do not add commentary or markdown fences.
    """
).strip()


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _contracts_payload(contracts: List[Dict[str, Any]], contract_ids: List[str]) -> List[Dict[str, Any]]:
    selected = [c for c in contracts if c["contract_id"] in set(contract_ids)]
    return [
        {
            "contract_id": c["contract_id"],
            "type": c["type"],
            "description": c["description"],
            "rationale": c["rationale"],
            "check_type": c["check_type"],
        }
        for c in selected
    ]


def build_generator_user_prompt(
    scenario: Dict[str, Any],
    modification_request: str,
    contract_ids: List[str],
    previous_state_doc: Dict[str, Any],
    current_code: str,
) -> str:
    contracts = _contracts_payload(scenario["contracts"], contract_ids)
    return dedent(
        f"""
        [Scenario]
        - scenario_id: {scenario["scenario_id"]}
        - track: {scenario["track"]}
        - source: {scenario["source"]}

        [Current Task]
        {modification_request}

        [Preserved Contracts]
        {_json_block(contracts)}

        [Previous State Document]
        {_json_block(previous_state_doc)}

        [Current Code]
        ```python
        {current_code}
        ```

        Update the code only. Return complete Python code and nothing else.
        """
    ).strip()


def build_state_doc_user_prompt(
    scenario: Dict[str, Any],
    step_id: int,
    loop_id: int,
    modification_request: str,
    contract_ids: List[str],
    previous_state_doc: Dict[str, Any],
    current_code: str,
) -> str:
    contracts = _contracts_payload(scenario["contracts"], contract_ids)
    template = dict(STATE_DOC_TEMPLATE)
    template["step_id"] = step_id
    template["loop_id"] = loop_id
    return dedent(
        f"""
        [Scenario]
        - scenario_id: {scenario["scenario_id"]}
        - step_id: {step_id}
        - loop_id: {loop_id}

        [Current Modification Request]
        {modification_request}

        [Preserved Contracts]
        {_json_block(contracts)}

        [Previous State Document]
        {_json_block(previous_state_doc)}

        [Current Code]
        ```python
        {current_code}
        ```

        [Required Output Schema]
        {_json_block(template)}
        """
    ).strip()


def build_evaluator_user_prompt(
    scenario: Dict[str, Any],
    step_id: int,
    loop_id: int,
    modification_request: str,
    contract_ids: List[str],
    state_document: Dict[str, Any],
    current_code: str,
    automated_signals: Dict[str, Any],
) -> str:
    contracts = _contracts_payload(scenario["contracts"], contract_ids)
    return dedent(
        f"""
        [Experiment Metadata]
        - scenario_id: {scenario["scenario_id"]}
        - step_id: {step_id}
        - loop_id: {loop_id}

        [Current Modification Request]
        {modification_request}

        [Expected Preserved Contracts]
        {_json_block(contracts)}

        [State Document]
        {_json_block(state_document)}

        [Current Code]
        ```python
        {current_code}
        ```

        [Automated Signals]
        {_json_block(automated_signals)}

        Evaluate task success, state alignment, and contract preservation.
        Return JSON only.
        """
    ).strip()


def build_refiner_user_prompt(
    scenario: Dict[str, Any],
    step_id: int,
    loop_id: int,
    modification_request: str,
    contract_ids: List[str],
    state_document: Dict[str, Any],
    current_code: str,
    automated_signals: Dict[str, Any],
    evaluator_result: Dict[str, Any],
) -> str:
    contracts = _contracts_payload(scenario["contracts"], contract_ids)
    return dedent(
        f"""
        [Experiment Metadata]
        - scenario_id: {scenario["scenario_id"]}
        - step_id: {step_id}
        - loop_id: {loop_id}

        [Current Modification Request]
        {modification_request}

        [Contracts To Preserve]
        {_json_block(contracts)}

        [Current State Document]
        {_json_block(state_document)}

        [Current Code]
        ```python
        {current_code}
        ```

        [Automated Signals]
        {_json_block(automated_signals)}

        [Evaluator Findings]
        {_json_block(evaluator_result)}

        Repair the code so that:
        - the current task is satisfied,
        - the preserved contracts remain true,
        - the code remains syntactically valid.
        """
    ).strip()


def build_syntax_fix_user_prompt(code: str, syntax_error: str) -> str:
    return dedent(
        f"""
        [Syntax Error]
        {syntax_error}

        [Broken Code]
        ```python
        {code}
        ```

        Return corrected complete Python code only.
        """
    ).strip()


def build_json_repair_user_prompt(raw_text: str) -> str:
    return dedent(
        f"""
        [Malformed Evaluator Output]
        {raw_text}

        Return one repaired JSON object only.
        """
    ).strip()
