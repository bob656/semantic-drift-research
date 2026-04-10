"""
metrics.py — 수치 계약 보존 실험 정량 지표

## 지표 정의

Drift Rate        : 전체 (단계×반복) 중 수치 계약 위반 발생 비율
Recovery Success  : Evaluator가 FAIL 판정 후 다음 단계에서 회복된 비율
Token Efficiency  : 컨텍스트 소모 토큰 대비 최종 보존율
ASL               : 시스템 붕괴(연속 2회 이상 FAIL) 전까지 유지된 평균 루프 수
"""
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class StepRecord:
    """단일 단계의 실행 기록"""
    step: int
    score: float                    # 0~10
    verdicts: Dict[str, str]        # {'INTEREST_RATE': 'PASS', ...}
    refinement_count: int = 0       # 이 단계에서 재시도 횟수
    tokens_used: int = 0            # 이 단계 소모 토큰 수 (interaction_log 기준)


@dataclass
class RunRecord:
    """단일 실험 실행(1 repeat) 기록"""
    agent_type: str
    steps: List[StepRecord] = field(default_factory=list)

    # ── 지표 계산 ──────────────────────────────────────────────

    @property
    def drift_rate(self) -> float:
        """전체 단계 중 FAIL이 하나라도 있는 단계 비율"""
        if not self.steps:
            return 0.0
        fail_steps = sum(
            1 for s in self.steps
            if any(v == 'FAIL' for v in s.verdicts.values())
        )
        return fail_steps / len(self.steps)

    @property
    def recovery_success(self) -> float:
        """
        FAIL 단계 다음 단계에서 PASS로 회복된 비율.
        마지막 단계 FAIL은 회복 불가 → 분모에서 제외.
        """
        recoveries = 0
        opportunities = 0
        for i in range(len(self.steps) - 1):
            cur = self.steps[i]
            nxt = self.steps[i + 1]
            cur_fail = any(v == 'FAIL' for v in cur.verdicts.values())
            if cur_fail:
                opportunities += 1
                nxt_pass = all(v == 'PASS' for v in nxt.verdicts.values())
                if nxt_pass:
                    recoveries += 1
        return recoveries / opportunities if opportunities > 0 else 1.0

    @property
    def token_efficiency(self) -> float:
        """토큰 1000개당 최종 보존 점수 (높을수록 효율적)"""
        total_tokens = sum(s.tokens_used for s in self.steps)
        if total_tokens == 0:
            return 0.0
        final_score = self.steps[-1].score if self.steps else 0.0
        return (final_score / 10.0) / (total_tokens / 1000)

    @property
    def asl(self) -> int:
        """
        Autonomous Stable Loops:
        연속으로 FAIL 없이 유지된 최대 루프(단계) 수.
        """
        max_streak = 0
        current_streak = 0
        for s in self.steps:
            if all(v == 'PASS' for v in s.verdicts.values()):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak

    @property
    def final_score(self) -> float:
        return self.steps[-1].score if self.steps else 0.0

    @property
    def scores(self) -> List[float]:
        return [s.score for s in self.steps]


class MetricsAggregator:
    """여러 실험 실행(N repeats)의 지표를 집계"""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.runs: List[RunRecord] = []

    def add_run(self, run: RunRecord) -> None:
        self.runs.append(run)

    def summary(self) -> Dict[str, Any]:
        if not self.runs:
            return {}

        def avg(values):
            return sum(values) / len(values) if values else 0.0

        def std(values):
            if len(values) < 2:
                return 0.0
            m = avg(values)
            return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5

        drift_rates       = [r.drift_rate        for r in self.runs]
        recovery_rates    = [r.recovery_success   for r in self.runs]
        token_efficiencies= [r.token_efficiency   for r in self.runs]
        asls              = [r.asl                for r in self.runs]
        final_scores      = [r.final_score        for r in self.runs]

        return {
            'agent_type':          self.agent_type,
            'n_runs':              len(self.runs),
            'drift_rate':          {'mean': avg(drift_rates),        'std': std(drift_rates)},
            'recovery_success':    {'mean': avg(recovery_rates),     'std': std(recovery_rates)},
            'token_efficiency':    {'mean': avg(token_efficiencies), 'std': std(token_efficiencies)},
            'asl':                 {'mean': avg(asls),               'std': std(asls)},
            'final_score':         {'mean': avg(final_scores),       'std': std(final_scores)},
            'drift_occurred_runs': sum(1 for d in drift_rates if d > 0),
        }

    def print_summary(self) -> None:
        s = self.summary()
        print(f"\n[{s['agent_type']}] ({s['n_runs']}회 반복)")
        print(f"  Drift Rate:       {s['drift_rate']['mean']:.3f} ± {s['drift_rate']['std']:.3f}")
        print(f"  Recovery Success: {s['recovery_success']['mean']:.3f} ± {s['recovery_success']['std']:.3f}")
        print(f"  Token Efficiency: {s['token_efficiency']['mean']:.4f} ± {s['token_efficiency']['std']:.4f}")
        print(f"  ASL:              {s['asl']['mean']:.1f} ± {s['asl']['std']:.1f}")
        print(f"  Final Score:      {s['final_score']['mean']:.2f} ± {s['final_score']['std']:.2f}")
        print(f"  드리프트 발생 실행: {s['drift_occurred_runs']}/{s['n_runs']}")
