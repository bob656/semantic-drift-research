"""
runner.py — 수치 계약 보존 실험 실행

## 실험 흐름

1. BaselineAgent와 NumericContractAgent 각각 num_repeats회 실행
2. 매 단계 후 NumericEvaluator로 수치 보존율 측정
3. 결과를 JSON으로 저장

## 측정 지표

  numeric_score  : 각 단계별 수치 보존 점수 (0~10)
  drift_rate     : (초기점수 - 최종점수) / 초기점수
  preservation_rate : 전체 단계에서 각 수치가 보존된 비율
"""
import os
import time
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from scenario import SCENARIO
from evaluator import NumericEvaluator
from cv_agents import BaselineAgent, NumericContractAgent


@dataclass
class NumericExperimentResult:
    agent_type: str
    scores: List[float]           # 단계별 수치 보존 점수 (0~10)
    drift_rate: float
    execution_times: List[float]
    details: List[List[str]]       # 단계별 수치별 결과 메시지
    contract_log: List[Dict] = field(default_factory=list)  # NumericContract 전용


class NumericExperimentRunner:

    def __init__(self, model: str, client: Any):
        self.model = model
        self.client = client
        self.evaluator = NumericEvaluator(SCENARIO['numeric_contracts'])
        self.debug_dir_base = os.path.join(
            os.path.dirname(__file__), '..', 'results', 'debug_constraint'
        )

    def run(self, num_repeats: int = 3,
            agents: List[str] = None) -> Dict[str, Any]:

        all_agents = {
            'Baseline': lambda: BaselineAgent(
                self.model, self.client, max_tokens=4096),
            'NumericContract': lambda: NumericContractAgent(
                self.model, self.client,
                known_contracts=SCENARIO['numeric_contracts'],
                max_tokens=4096),
        }
        selected = agents or list(all_agents.keys())

        results = {'scenario': SCENARIO['name']}
        for name in selected:
            results[name] = []

        print(f"\n🔢 수치 계약 보존 실험 시작")
        print(f"모델: {self.model} | 반복: {num_repeats}")
        print(f"시나리오: {SCENARIO['name']}")
        print("=" * 60)

        for repeat in range(num_repeats):
            print(f"\n📊 실험 {repeat + 1}/{num_repeats}")
            print("-" * 40)
            for name in selected:
                print(f"🔍 {name} 에이전트 실행 중...")
                agent = all_agents[name]()
                result = self._run_single(agent, name, repeat + 1)
                results[name].append(result)
                print(f"   → 드리프트: {result.drift_rate:.3f} | "
                      f"최종 점수: {result.scores[-1]:.1f}/10")

        return results

    def _run_single(self, agent, agent_type: str,
                    repeat: int) -> NumericExperimentResult:
        execution_times = []
        all_details = []

        debug_dir = os.path.join(
            self.debug_dir_base, f"{agent_type.lower()}_r{repeat}")
        os.makedirs(debug_dir, exist_ok=True)

        # 초기 코드 생성
        start = time.time()
        current_code = agent.solve_initial(SCENARIO['initial_task'])
        execution_times.append(time.time() - start)
        self._save_code(debug_dir, 'step0_initial.py', current_code)

        score, details = self.evaluator.evaluate(current_code)
        scores = [score]
        all_details.append(details)
        self._print_step(0, score, details)

        # 수정 단계
        for i, modification in enumerate(SCENARIO['modifications'], 1):
            print(f"   → 수정 {i}/{len(SCENARIO['modifications'])}: "
                  f"{modification[:50]}...")
            start = time.time()
            current_code = agent.modify_code_with_syntax_retry(
                current_code, modification)
            execution_times.append(time.time() - start)
            self._save_code(debug_dir, f'step{i}_mod{i}.py', current_code)

            score, details = self.evaluator.evaluate(current_code)
            scores.append(score)
            all_details.append(details)
            self._print_step(i, score, details)

        drift_rate = self._calc_drift(scores)
        contract_log = getattr(agent, 'contract_log', [])

        return NumericExperimentResult(
            agent_type=agent_type,
            scores=scores,
            drift_rate=drift_rate,
            execution_times=execution_times,
            details=all_details,
            contract_log=contract_log,
        )

    def _calc_drift(self, scores: List[float]) -> float:
        if not scores or scores[0] == 0:
            return 0.0
        return (scores[0] - scores[-1]) / scores[0]

    def _print_step(self, step: int, score: float,
                    details: List[str]) -> None:
        print(f"      [step{step}] 점수: {score:.1f}/10")
        for d in details:
            mark = "✓" if "PRESERVED" in d else ("?" if "MISSING" in d else "✗")
            print(f"         {mark} {d}")

    def _save_code(self, directory: str, filename: str, code: str) -> None:
        path = os.path.join(directory, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)


def save_results(results: Dict, args) -> str:
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'results'),
                exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(
        os.path.dirname(__file__), '..', 'results',
        f"constraint_{timestamp}.json"
    )

    output = {
        'metadata': {
            'timestamp': timestamp,
            'model': args.model,
            'host': args.host,
            'repeats': args.repeats,
            'scenario': SCENARIO['name'],
            'numeric_contracts': SCENARIO['numeric_contracts'],
        },
        'raw_results': {
            name: [
                {
                    'scores': r.scores,
                    'drift_rate': r.drift_rate,
                    'execution_times': r.execution_times,
                    'details': r.details,
                    'contract_log': r.contract_log,
                }
                for r in result_list
            ]
            for name, result_list in results.items()
            if name != 'scenario'
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 결과 저장: {filename}")
    return filename
