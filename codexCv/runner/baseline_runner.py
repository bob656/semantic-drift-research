from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from .load_scenario import load_prompt, load_scenario
from .prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    CODE_GENERATOR_SYSTEM_PROMPT,
    CODE_REFINER_SYSTEM_PROMPT,
    JSON_REPAIR_SYSTEM_PROMPT,
    STATE_DOC_UPDATER_SYSTEM_PROMPT,
    SYNTAX_FIXER_SYSTEM_PROMPT,
    build_evaluator_user_prompt,
    build_generator_user_prompt,
    build_json_repair_user_prompt,
    build_refiner_user_prompt,
    build_state_doc_user_prompt,
    build_syntax_fix_user_prompt,
)
from .state_doc import (
    fresh_state_doc,
    normalize_state_doc,
    render_state_doc_markdown,
    synthesize_state_doc_from_code,
)


DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_HOST = "http://192.168.100.52:11434"


class LLMClient(Protocol):
    def chat(self, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]) -> Dict[str, Any]:
        ...


class CheckProvider(Protocol):
    def run_checks(
        self,
        scenario: Dict[str, Any],
        step: Dict[str, Any],
        code: str,
        state_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...


@dataclass
class AutomatedChecks:
    syntax_ok: bool
    syntax_error: Optional[str]
    task_pass_rate: Optional[float]
    contract_pass_rate: Optional[float]
    task_test_results: List[Dict[str, Any]]
    contract_test_results: List[Dict[str, Any]]
    static_probe_results: List[Dict[str, Any]]


@dataclass
class EvaluatorResult:
    task_success: int
    state_alignment: int
    contract_preservation: int
    severity: str
    drift_detected: bool
    findings: List[Dict[str, Any]]
    repair_priority: List[str]
    summary: str


@dataclass
class LoopRecord:
    loop_id: int
    generator_raw: str
    state_doc_raw: str
    evaluator_raw: str
    state_document: Dict[str, Any]
    code: str
    automated_checks: AutomatedChecks
    evaluator_result: EvaluatorResult
    refinement_triggered: bool
    prompt_tokens_estimate: Dict[str, int]


@dataclass
class StepRecord:
    step_id: int
    request: str
    contracts_checked: List[str]
    loops: List[LoopRecord] = field(default_factory=list)
    final_state_document: Dict[str, Any] = field(default_factory=dict)
    final_code: str = ""


@dataclass
class RunMetrics:
    drift_rate: float
    recovery_success: float
    token_efficiency: float
    asl: int
    first_drift_step: Optional[int]
    false_state_rate: float
    stale_state_rate: float
    task_drift_decoupling_rate: float


class NullCheckProvider:
    """
    Placeholder automated checker.

    It performs syntax validation and leaves task/contract execution as unknown
    until wired to a real executor.
    """

    def run_checks(
        self,
        scenario: Dict[str, Any],
        step: Dict[str, Any],
        code: str,
        state_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        syntax_ok = True
        syntax_error = None
        try:
            ast.parse(code)
        except SyntaxError as exc:
            syntax_ok = False
            syntax_error = str(exc)

        probe_results = []
        for contract in scenario["contracts"]:
            if contract["contract_id"] not in step["contracts_checked"]:
                continue
            result = {
                "contract_id": contract["contract_id"],
                "check_type": contract["check_type"],
                "status": "unknown",
                "details": "No runtime executor wired yet.",
            }

            if contract["check_type"] == "ast" and syntax_ok:
                result["status"] = "pass" if _run_ast_probe(step, contract, code) else "fail"
                result["details"] = "AST probe executed."
            probe_results.append(result)

        task_results = [
            {"target": target, "status": "unknown"}
            for target in step["task_tests"]
        ]
        contract_results = [
            {"target": probe["contract_id"], "status": probe["status"]}
            for probe in probe_results
        ]

        task_pass_rate = None
        contract_pass_rate = _fraction_pass(contract_results)

        return {
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_error,
            "task_pass_rate": task_pass_rate,
            "contract_pass_rate": contract_pass_rate,
            "task_test_results": task_results,
            "contract_test_results": contract_results,
            "static_probe_results": probe_results,
        }


class ExecCheckProvider:
    """Execute scenario task tests and contract tests against generated code."""

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def run_checks(
        self,
        scenario: Dict[str, Any],
        step: Dict[str, Any],
        code: str,
        state_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        syntax_ok = True
        syntax_error = None
        try:
            ast.parse(code)
        except SyntaxError as exc:
            syntax_ok = False
            syntax_error = str(exc)

        scenario_dir = Path(scenario["_scenario_dir"])
        task_results = []
        contract_results = []
        static_probe_results = []

        if syntax_ok:
            for target in step["task_tests"]:
                task_results.extend(self._run_python_checks(scenario_dir, target, code))

            for contract in scenario["contracts"]:
                if contract["contract_id"] not in step["contracts_checked"]:
                    continue
                if contract["check_type"] == "ast":
                    passed = _run_ast_probe(step, contract, code)
                    static_probe_results.append(
                        {
                            "contract_id": contract["contract_id"],
                            "check_type": "ast",
                            "status": "pass" if passed else "fail",
                            "details": contract["check_target"],
                        }
                    )
                    contract_results.append(
                        {
                            "target": contract["contract_id"],
                            "status": "pass" if passed else "fail",
                        }
                    )
                else:
                    target = contract["check_target"].split("::", 1)[0]
                    contract_results.extend(
                        self._run_python_checks(
                            scenario_dir,
                            target,
                            code,
                            requested_name=contract["check_target"].split("::", 1)[1],
                            target_override=contract["contract_id"],
                        )
                    )
        else:
            for target in step["task_tests"]:
                task_results.append({"target": target, "status": "fail", "details": syntax_error})
            for contract in scenario["contracts"]:
                if contract["contract_id"] in step["contracts_checked"]:
                    contract_results.append(
                        {
                            "target": contract["contract_id"],
                            "status": "fail",
                            "details": syntax_error,
                        }
                    )

        return {
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_error,
            "task_pass_rate": _fraction_pass(task_results),
            "contract_pass_rate": _fraction_pass(contract_results),
            "task_test_results": task_results,
            "contract_test_results": contract_results,
            "static_probe_results": static_probe_results,
        }

    def _run_python_checks(
        self,
        scenario_dir: Path,
        relative_target: str,
        code: str,
        requested_name: Optional[str] = None,
        target_override: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        test_path = scenario_dir / relative_target
        runner_code = """
import importlib.util
import json
import sys
from pathlib import Path

candidate_path = Path(sys.argv[1])
test_path = Path(sys.argv[2])
requested_name = None if sys.argv[3] == "__ALL__" else sys.argv[3]

candidate_spec = importlib.util.spec_from_file_location("candidate_module", candidate_path)
candidate = importlib.util.module_from_spec(candidate_spec)
sys.modules[candidate_spec.name] = candidate
candidate_spec.loader.exec_module(candidate)

test_spec = importlib.util.spec_from_file_location("scenario_test_module", test_path)
test_module = importlib.util.module_from_spec(test_spec)
sys.modules[test_spec.name] = test_module
test_spec.loader.exec_module(test_module)

results = test_module.run_checks(candidate)
if requested_name is not None:
    results = [r for r in results if r.get("target") == requested_name]
print(json.dumps(results))
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            candidate_path = tmpdir_path / "candidate.py"
            candidate_path.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    runner_code,
                    str(candidate_path),
                    str(test_path),
                    requested_name or "__ALL__",
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

        if proc.returncode != 0:
            details = proc.stderr.strip() or proc.stdout.strip() or "subprocess failed"
            return [
                {
                    "target": target_override or relative_target,
                    "status": "fail",
                    "details": details,
                }
            ]

        try:
            results = json.loads(proc.stdout.strip() or "[]")
        except json.JSONDecodeError:
            return [
                {
                    "target": target_override or relative_target,
                    "status": "fail",
                    "details": f"invalid JSON from test runner: {proc.stdout[:300]}",
                }
            ]

        normalized = []
        for result in results:
            normalized.append(
                {
                    "target": target_override or result.get("target", relative_target),
                    "status": result.get("status", "unknown"),
                    "details": result.get("details", ""),
                }
            )
        return normalized


def _run_ast_probe(step: Dict[str, Any], contract: Dict[str, Any], code: str) -> bool:
    target = contract["check_target"]
    probe_name = target.split("::")[-1]
    if probe_name == "check_create_order_signature":
        return _check_signature(code, "create_order", ["self", "customer", "items"])
    if probe_name == "check_add_expense_signature":
        return _check_signature(code, "add_expense", ["self", "category", "amount"])
    if probe_name == "check_extract_span_signature":
        return _check_signature_prefix(
            code,
            "extract_span",
            [["text", "start", "end"], ["text", "start", "end", "normalize_whitespace"]],
        )
    if probe_name == "check_final_price_signature":
        return _check_signature_prefix(
            code,
            "final_price",
            [["price", "discount_percent"], ["price", "discount_percent", "tax_percent"]],
        )
    return False


def _check_signature(code: str, fn_name: str, expected: List[str]) -> bool:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            args = [arg.arg for arg in node.args.args]
            return args[: len(expected)] == expected
    return False


def _check_signature_prefix(code: str, fn_name: str, allowed_prefixes: List[List[str]]) -> bool:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            args = [arg.arg for arg in node.args.args]
            return any(args[: len(prefix)] == prefix for prefix in allowed_prefixes)
    return False


def _fraction_pass(results: List[Dict[str, Any]]) -> Optional[float]:
    if not results:
        return None
    known = [r for r in results if r["status"] in {"pass", "fail"}]
    if not known:
        return None
    return sum(1 for r in known if r["status"] == "pass") / len(known)


class BaselineHarnessRunner:
    def __init__(
        self,
        model: str,
        client: LLMClient,
        check_provider: Optional[CheckProvider] = None,
        max_refinements: int = 2,
        output_dir: Optional[str] = None,
        num_predict: int = 2048,
    ) -> None:
        self.model = model
        self.client = client
        self.check_provider = check_provider or NullCheckProvider()
        self.max_refinements = max_refinements
        self.output_dir = Path(output_dir or "codexCv/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.num_predict = num_predict

    def run(self, scenario_id: str) -> Dict[str, Any]:
        scenario = load_scenario(scenario_id)
        steps = [_step0_as_step(scenario)] + scenario["steps"]
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifact_dir = self.output_dir / f"{scenario['scenario_id']}_{run_timestamp}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        state_document = fresh_state_doc()
        current_code = ""
        step_records: List[StepRecord] = []

        for step in steps:
            request = load_prompt(scenario_id, step["prompt_file"])
            record, state_document, current_code = self._run_step(
                scenario=scenario,
                step=step,
                request=request,
                current_code=current_code,
                state_document=state_document,
                artifact_dir=artifact_dir,
            )
            step_records.append(record)

        metrics = _compute_metrics(step_records)
        run_record = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "scenario_id": scenario_id,
                "model": self.model,
                "max_refinements": self.max_refinements,
            },
            "steps": [asdict(record) for record in step_records],
            "metrics": asdict(metrics),
        }
        output_path = self._write_results(run_record, scenario["scenario_id"], run_timestamp)
        run_record["output_path"] = str(output_path)
        run_record["artifact_dir"] = str(artifact_dir)
        return run_record

    def _run_step(
        self,
        scenario: Dict[str, Any],
        step: Dict[str, Any],
        request: str,
        current_code: str,
        state_document: Dict[str, Any],
        artifact_dir: Path,
    ) -> Tuple[StepRecord, Dict[str, Any], str]:
        step_record = StepRecord(
            step_id=step["step_id"],
            request=request,
            contracts_checked=list(step["contracts_checked"]),
        )

        loop_id = 1
        working_code = current_code
        working_state = state_document
        latest_eval: Optional[EvaluatorResult] = None

        while True:
            if loop_id == 1:
                system_prompt = CODE_GENERATOR_SYSTEM_PROMPT
                user_prompt = build_generator_user_prompt(
                    scenario=scenario,
                    modification_request=request,
                    contract_ids=step["contracts_checked"],
                    previous_state_doc=working_state,
                    current_code=working_code,
                )
            else:
                system_prompt = CODE_REFINER_SYSTEM_PROMPT
                user_prompt = build_refiner_user_prompt(
                    scenario=scenario,
                    step_id=step["step_id"],
                    loop_id=loop_id,
                    modification_request=request,
                    contract_ids=step["contracts_checked"],
                    state_document=working_state,
                    current_code=working_code,
                    automated_signals=asdict(step_record.loops[-1].automated_checks),
                    evaluator_result=asdict(latest_eval) if latest_eval else {},
                )

            raw_output = self._call_llm(system_prompt, user_prompt)
            next_code = _extract_code_output(raw_output)
            next_code = self._stabilize_code(next_code)
            state_doc_raw = self._call_llm(
                STATE_DOC_UPDATER_SYSTEM_PROMPT,
                build_state_doc_user_prompt(
                    scenario=scenario,
                    step_id=step["step_id"],
                    loop_id=loop_id,
                    modification_request=request,
                    contract_ids=step["contracts_checked"],
                    previous_state_doc=working_state,
                    current_code=next_code,
                ),
                num_predict=min(self.num_predict, 384),
            )
            next_state = _parse_state_doc_output(
                state_doc_raw=state_doc_raw,
                code=next_code,
                previous_state_doc=working_state,
                contracts=[c for c in scenario["contracts"] if c["contract_id"] in step["contracts_checked"]],
                step_id=step["step_id"],
                loop_id=loop_id,
            )
            checks = AutomatedChecks(**self.check_provider.run_checks(
                scenario=scenario,
                step=step,
                code=next_code,
                state_document=next_state,
            ))
            evaluator_prompt = build_evaluator_user_prompt(
                scenario=scenario,
                step_id=step["step_id"],
                loop_id=loop_id,
                modification_request=request,
                contract_ids=step["contracts_checked"],
                state_document=next_state,
                current_code=next_code,
                automated_signals=asdict(checks),
            )
            evaluator_raw = self._call_llm(
                EVALUATOR_SYSTEM_PROMPT,
                evaluator_prompt,
                num_predict=min(self.num_predict, 384),
            )
            latest_eval = EvaluatorResult(**_parse_evaluator_json(evaluator_raw))
            if latest_eval.summary == "Invalid evaluator output.":
                repaired_evaluator_raw = self._call_llm(
                    JSON_REPAIR_SYSTEM_PROMPT,
                    build_json_repair_user_prompt(evaluator_raw),
                    num_predict=256,
                )
                latest_eval = EvaluatorResult(**_parse_evaluator_json(repaired_evaluator_raw))
                evaluator_raw = repaired_evaluator_raw

            refinement_needed = _needs_refinement(checks, latest_eval)
            if loop_id >= self.max_refinements + 1:
                refinement_needed = False

            loop_record = LoopRecord(
                loop_id=loop_id,
                generator_raw=raw_output,
                state_doc_raw=state_doc_raw,
                evaluator_raw=evaluator_raw,
                state_document=next_state,
                code=next_code,
                automated_checks=checks,
                evaluator_result=latest_eval,
                refinement_triggered=refinement_needed,
                prompt_tokens_estimate={
                    "generator_prompt_chars": len(user_prompt),
                    "evaluator_prompt_chars": len(evaluator_prompt),
                },
            )
            step_record.loops.append(loop_record)
            self._write_loop_artifacts(
                artifact_dir=artifact_dir,
                step_id=step["step_id"],
                loop_id=loop_id,
                request=request,
                state_document=next_state,
                code=next_code,
                state_doc_raw=state_doc_raw,
                checks=checks,
                evaluator_raw=evaluator_raw,
                evaluator_result=latest_eval,
            )

            working_state = next_state
            working_code = next_code

            if not refinement_needed:
                break
            loop_id += 1

        step_record.final_state_document = working_state
        step_record.final_code = working_code
        return step_record, working_state, working_code

    def _call_llm(self, system_prompt: str, user_prompt: str, num_predict: Optional[int] = None) -> str:
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.2, "num_predict": num_predict or self.num_predict},
        )
        return response["message"]["content"]

    def _stabilize_code(self, code: str) -> str:
        current = code
        for _ in range(2):
            try:
                ast.parse(current)
                return current
            except SyntaxError as exc:
                current = _extract_code_output(
                    self._call_llm(
                        SYNTAX_FIXER_SYSTEM_PROMPT,
                        build_syntax_fix_user_prompt(current, str(exc)),
                        num_predict=min(self.num_predict, 256),
                    )
                )
        return current

    def _write_results(self, record: Dict[str, Any], scenario_name: str, run_timestamp: str) -> Path:
        path = self.output_dir / f"{scenario_name}_{run_timestamp}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def _write_loop_artifacts(
        self,
        artifact_dir: Path,
        step_id: int,
        loop_id: int,
        request: str,
        state_document: Dict[str, Any],
        code: str,
        state_doc_raw: str,
        checks: AutomatedChecks,
        evaluator_raw: str,
        evaluator_result: EvaluatorResult,
    ) -> None:
        loop_dir = artifact_dir / f"step{step_id}_loop{loop_id}"
        loop_dir.mkdir(parents=True, exist_ok=True)

        (loop_dir / "request.md").write_text(request, encoding="utf-8")
        (loop_dir / "state_document.json").write_text(
            json.dumps(state_document, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (loop_dir / "state_document.md").write_text(
            render_state_doc_markdown(state_document),
            encoding="utf-8",
        )
        (loop_dir / "state_document_raw.txt").write_text(state_doc_raw, encoding="utf-8")
        (loop_dir / "candidate.py").write_text(code, encoding="utf-8")
        (loop_dir / "automated_checks.json").write_text(
            json.dumps(asdict(checks), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (loop_dir / "evaluator_raw.txt").write_text(evaluator_raw, encoding="utf-8")
        (loop_dir / "evaluator.json").write_text(
            json.dumps(asdict(evaluator_result), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _step0_as_step(scenario: Dict[str, Any]) -> Dict[str, Any]:
    all_contracts = [contract["contract_id"] for contract in scenario["contracts"]]
    return {
        "step_id": 0,
        "prompt_file": scenario["step0"]["prompt_file"],
        "task_tests": scenario["step0"]["task_tests"],
        "contracts_checked": all_contracts,
    }


def _extract_code_output(text: str) -> str:
    marked = re.search(r"<<UPDATED_CODE>>(.*?)<<END_UPDATED_CODE>>", text, re.DOTALL)
    if marked:
        return _strip_code_fence(marked.group(1).strip())

    fenced = re.search(r"```python(.*?)```", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    generic = re.search(r"```(.*?)```", text, re.DOTALL)
    if generic:
        return generic.group(1).strip()

    return text.strip()


def _strip_code_fence(text: str) -> str:
    code = text
    if "```python" in code:
        code = code.split("```python", 1)[1]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def _parse_state_doc_output(
    state_doc_raw: str,
    code: str,
    previous_state_doc: Dict[str, Any],
    contracts: List[Dict[str, Any]],
    step_id: int,
    loop_id: int,
) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", state_doc_raw, re.DOTALL)
    if match:
        try:
            return normalize_state_doc(json.loads(match.group(0)), step_id=step_id, loop_id=loop_id)
        except json.JSONDecodeError:
            pass

    return synthesize_state_doc_from_code(
        code=code,
        previous_state_doc=previous_state_doc,
        contracts=contracts,
        step_id=step_id,
        loop_id=loop_id,
        reason="LLM state document was missing or malformed.",
    )


def _parse_evaluator_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return _fallback_evaluator_json(text, "Evaluator did not return valid JSON.")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return _fallback_evaluator_json(text, "Evaluator returned malformed JSON.")


def _fallback_evaluator_json(text: str, message: str) -> Dict[str, Any]:
    return {
        "task_success": 0,
        "state_alignment": 0,
        "contract_preservation": 0,
        "severity": "critical",
        "drift_detected": True,
        "findings": [
            {
                "type": "unknown",
                "severity": "critical",
                "location": "unknown",
                "message": message,
                "evidence": text[:300],
            }
        ],
        "repair_priority": ["Return valid evaluator JSON."],
        "summary": "Invalid evaluator output.",
    }


def _needs_refinement(checks: AutomatedChecks, eval_result: EvaluatorResult) -> bool:
    if not checks.syntax_ok:
        return True
    if eval_result.severity in {"fail", "critical"}:
        return True
    if eval_result.task_success < 8:
        return True
    if eval_result.state_alignment < 9:
        return True
    if eval_result.contract_preservation < 10:
        return True
    return False


def _compute_metrics(step_records: List[StepRecord]) -> RunMetrics:
    total_loops = sum(len(step.loops) for step in step_records)
    if total_loops == 0:
        return RunMetrics(0.0, 0.0, 0.0, 0, None, 0.0, 0.0, 0.0)

    drift_loops = 0
    recovered = 0
    total_tokens = 0
    first_drift_step = None
    false_state_findings = 0
    stale_state_findings = 0
    total_findings = 0
    task_drift_decoupled = 0
    sustainable_loops = 0

    for step in step_records:
        step_had_drift = False
        step_recovered = False
        for loop in step.loops:
            total_tokens += sum(loop.prompt_tokens_estimate.values())
            if loop.evaluator_result.drift_detected:
                drift_loops += 1
                step_had_drift = True
                if first_drift_step is None:
                    first_drift_step = step.step_id
            if (
                loop.evaluator_result.task_success >= 8
                and loop.evaluator_result.contract_preservation < 10
            ):
                task_drift_decoupled += 1
            for finding in loop.evaluator_result.findings:
                total_findings += 1
                message = finding.get("message", "").lower()
                if "state" in finding.get("type", "") and "not supported" in message:
                    false_state_findings += 1
                if "stale" in message or "outdated" in message:
                    stale_state_findings += 1
            if loop.evaluator_result.severity not in {"critical"}:
                sustainable_loops += 1
            if step_had_drift and not loop.evaluator_result.drift_detected:
                step_recovered = True
        if step_had_drift and step_recovered:
            recovered += 1

    drift_rate = drift_loops / total_loops
    recovery_success = recovered / max(sum(1 for step in step_records if any(loop.evaluator_result.drift_detected for loop in step.loops)), 1)
    token_efficiency = (total_loops - drift_loops) / max(total_tokens / 1000, 1e-9)
    false_state_rate = false_state_findings / max(total_findings, 1)
    stale_state_rate = stale_state_findings / max(total_findings, 1)
    task_drift_decoupling_rate = task_drift_decoupled / total_loops

    return RunMetrics(
        drift_rate=drift_rate,
        recovery_success=recovery_success,
        token_efficiency=token_efficiency,
        asl=sustainable_loops,
        first_drift_step=first_drift_step,
        false_state_rate=false_state_rate,
        stale_state_rate=stale_state_rate,
        task_drift_decoupling_rate=task_drift_decoupling_rate,
    )


def make_client(host: str, timeout: int = 600) -> LLMClient:
    from ollama import Client

    return Client(host=host, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run codexCv baseline harness")
    parser.add_argument("--scenario", required=True, help="e.g. controlled/order_system_v1")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-refinements", type=int, default=2)
    parser.add_argument("--output-dir", default="codexCv/results")
    parser.add_argument("--check-mode", choices=["exec", "null"], default="exec")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--num-predict", type=int, default=1024)
    args = parser.parse_args()

    client = make_client(args.host, timeout=args.timeout)
    check_provider = ExecCheckProvider() if args.check_mode == "exec" else NullCheckProvider()
    runner = BaselineHarnessRunner(
        model=args.model,
        client=client,
        check_provider=check_provider,
        max_refinements=args.max_refinements,
        output_dir=args.output_dir,
        num_predict=args.num_predict,
    )
    result = runner.run(args.scenario)
    print(json.dumps({
        "scenario_id": result["metadata"]["scenario_id"],
        "metrics": result["metrics"],
        "output_path": result["output_path"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
