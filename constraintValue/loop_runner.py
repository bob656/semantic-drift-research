"""
loop_runner.py — 4단계 순환 평가 워크플로우

## 워크플로우

Phase 1 (Planning)  : 수치 계약 스키마 정의 (시나리오 로드)
Phase 2 (Execution) : Generator가 코드 생성/수정
Phase 3 (Critique)  : Evaluator가 수치 계약 준수 여부 판정
Phase 4 (Refinement): 점수 < threshold → Phase 2로 재시도 (최대 max_retries회)

## 측정 지표 (metrics.py)

  Drift Rate        : 위반 발생 단계 비율
  Recovery Success  : FAIL 후 다음 단계 회복 비율
  Token Efficiency  : 토큰 1000개당 보존율
  ASL               : 연속 안정 루프 수

## 논문 연결

IEEE-ISTAS 2025: "반복 정제 시 제약 조건 37.6% 악화"
  → Baseline이 재시도 없이 단순 수정 → Drift Rate 측정
  → NumericContract가 수치 고정 + Evaluator 루프 → Drift Rate 감소
"""
import os
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from scenario import SCENARIO
from eval_agent import EvaluatorAgent
from cv_agents import BaselineAgent, NumericContractAgent
from metrics import MetricsAggregator, RunRecord, StepRecord


# 정제 기준 점수 (이 미만이면 재시도)
DEFAULT_THRESHOLD = 7.0
DEFAULT_MAX_RETRIES = 2


class LoopRunner:
    """
    4단계 순환 평가 워크플로우 실행기.

    Generator (Baseline 또는 NumericContract) +
    Evaluator (EvaluatorAgent) 쌍으로 실험을 진행한다.
    """

    def __init__(self, model: str, client: Any,
                 threshold: float = DEFAULT_THRESHOLD,
                 max_retries: int = DEFAULT_MAX_RETRIES):
        self.model = model
        self.client = client
        self.threshold = threshold
        self.max_retries = max_retries
        self.evaluator = EvaluatorAgent(model=model, client=client)

    def run(self, num_repeats: int = 3,
            agents: Optional[List[str]] = None) -> Dict[str, Any]:

        all_agents = {
            'Baseline': lambda: BaselineAgent(
                self.model, self.client, max_tokens=4096),
            'NumericContract': lambda: NumericContractAgent(
                self.model, self.client,
                known_contracts=SCENARIO['numeric_contracts'],
                max_tokens=4096),
        }
        selected = agents or list(all_agents.keys())

        aggregators = {name: MetricsAggregator(name) for name in selected}

        print(f"\n🔄 4단계 순환 평가 실험 시작")
        print(f"모델: {self.model} | 반복: {num_repeats}")
        print(f"기준 점수: {self.threshold}/10 | 최대 재시도: {self.max_retries}회")
        print("=" * 60)

        for repeat in range(num_repeats):
            print(f"\n📊 실험 {repeat + 1}/{num_repeats}")
            print("-" * 40)
            for name in selected:
                print(f"🔍 {name} ...")
                generator = all_agents[name]()
                run_record = self._run_single(generator, name, repeat + 1)
                aggregators[name].add_run(run_record)
                print(f"   Drift={run_record.drift_rate:.3f} | "
                      f"ASL={run_record.asl} | "
                      f"Final={run_record.final_score:.1f}/10")

        return aggregators

    # ── 단일 실험 ─────────────────────────────────────────────

    def _run_single(self, generator, agent_type: str,
                    repeat: int) -> RunRecord:
        run = RunRecord(agent_type=agent_type)
        contracts = SCENARIO['numeric_contracts']

        debug_dir = os.path.join(
            os.path.dirname(__file__), '..', 'results',
            f"debug_loop_{agent_type.lower()}_r{repeat}"
        )
        os.makedirs(debug_dir, exist_ok=True)

        # ── Phase 1: Planning ──────────────────────────────────
        print(f"   [Phase1] 계획 — 수치 계약 {len(contracts)}개 로드")

        # ── Phase 2 + 3 + 4: step0 초기 코드 ─────────────────
        current_code = self._execute_and_critique(
            generator=generator,
            step_index=0,
            modification_request=SCENARIO['initial_task'],
            current_code=None,
            contracts=contracts,
            debug_dir=debug_dir,
            run=run,
        )

        # ── 수정 단계 반복 ────────────────────────────────────
        for i, modification in enumerate(SCENARIO['modifications'], 1):
            print(f"   [step{i}] {modification[:50]}...")
            current_code = self._execute_and_critique(
                generator=generator,
                step_index=i,
                modification_request=modification,
                current_code=current_code,
                contracts=contracts,
                debug_dir=debug_dir,
                run=run,
            )

        return run

    def _execute_and_critique(
        self,
        generator,
        step_index: int,
        modification_request: str,
        current_code: Optional[str],
        contracts: Dict[str, float],
        debug_dir: str,
        run: RunRecord,
    ) -> str:
        """
        Phase 2 (Execution) → Phase 3 (Critique) → Phase 4 (Refinement) 루프.
        점수 >= threshold가 될 때까지 또는 max_retries 도달 시까지 반복.
        """
        refinement_count = 0
        code = current_code

        for attempt in range(self.max_retries + 1):
            # ── Phase 2: Execution ─────────────────────────────
            if step_index == 0:
                code = generator.solve_initial(modification_request)
            else:
                code = generator.modify_code_with_syntax_retry(
                    code, modification_request)

            self._save_code(
                debug_dir,
                f"step{step_index}_attempt{attempt}.py",
                code
            )

            # ── Phase 3: Critique ──────────────────────────────
            score, details, verdicts = self.evaluator.evaluate(
                code=code,
                contracts=contracts,
                step_index=step_index,
                modification_request=modification_request if step_index > 0 else "",
            )

            verdict_map = {name: v for name, (v, _) in verdicts.items()}
            tokens = self._count_tokens(generator)

            for d in details:
                mark = "✓" if "PASS" in d else "✗"
                print(f"      {mark} {d}")
            print(f"      → 점수: {score:.1f}/10 (시도 {attempt+1})")

            # ── Phase 4: Refinement 결정 ───────────────────────
            if score >= self.threshold or attempt >= self.max_retries:
                # 기준 통과 or 재시도 한계 → 이 결과로 확정
                step_record = StepRecord(
                    step=step_index,
                    score=score,
                    verdicts=verdict_map,
                    refinement_count=refinement_count,
                    tokens_used=tokens,
                )
                run.steps.append(step_record)
                return code

            # 기준 미달 → 재시도
            refinement_count += 1
            fail_details = [
                d for d in details if "FAIL" in d
            ]
            feedback = "\n".join(fail_details)
            print(f"      ⚠ 기준 미달 ({score:.1f} < {self.threshold}) → 재시도 {refinement_count}")

            # Refinement 피드백을 수정 요청에 추가
            modification_request = (
                f"{modification_request}\n\n"
                f"[평가자 피드백 — 반드시 수정]\n{feedback}"
            )

        # 도달 불가 (안전장치)
        return code

    def _count_tokens(self, generator) -> int:
        """interaction_log에서 이번 단계까지 소모된 토큰 수 추정"""
        # 각 호출의 prompt + response 문자 수 합산 (토큰 ≈ 문자 / 3.5)
        total_chars = sum(
            len(entry.get('prompt_preview', '')) +
            len(entry.get('response_preview', ''))
            for entry in generator.interaction_log
        )
        return int(total_chars / 3.5)

    def _save_code(self, directory: str, filename: str, code: str) -> None:
        path = os.path.join(directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)


def save_results(aggregators: Dict[str, MetricsAggregator], args) -> str:
    os.makedirs(
        os.path.join(os.path.dirname(__file__), '..', 'results'),
        exist_ok=True
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(
        os.path.dirname(__file__), '..', 'results',
        f"loop_{timestamp}.json"
    )

    output = {
        'metadata': {
            'timestamp': timestamp,
            'model': args.model,
            'host': args.host,
            'repeats': args.repeats,
            'threshold': args.threshold,
            'max_retries': args.max_retries,
            'scenario': SCENARIO['name'],
            'numeric_contracts': SCENARIO['numeric_contracts'],
        },
        'summaries': {
            name: agg.summary()
            for name, agg in aggregators.items()
        },
        'raw_runs': {
            name: [
                {
                    'drift_rate': r.drift_rate,
                    'recovery_success': r.recovery_success,
                    'token_efficiency': r.token_efficiency,
                    'asl': r.asl,
                    'final_score': r.final_score,
                    'scores': r.scores,
                    'steps': [
                        {
                            'step': s.step,
                            'score': s.score,
                            'verdicts': s.verdicts,
                            'refinement_count': s.refinement_count,
                            'tokens_used': s.tokens_used,
                        }
                        for s in r.steps
                    ]
                }
                for r in agg.runs
            ]
            for name, agg in aggregators.items()
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 결과 저장: {filename}")
    return filename
