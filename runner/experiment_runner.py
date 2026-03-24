import time
from dataclasses import dataclass
from typing import List, Dict, Any
from agents import BaselineAgent, StateDocAgent
from evaluator import CodeEvaluator

@dataclass
class ExperimentResult:
    """실험 결과 데이터 클래스"""
    agent_type: str
    scores: List[float]
    drift_rate: float
    execution_times: List[float]
    interaction_log: List[Dict[str, Any]]

class ExperimentRunner:
    """실험 실행 및 관리 클래스"""

    def __init__(self, model: str, client: Any):
        self.model = model
        self.client = client
        self.evaluator = CodeEvaluator(model=model, client=client)

        # StudentManager 진화 시나리오 정의
        self.scenario = {
            'name': 'StudentManager Evolution',
            'description': '학생 관리 시스템의 단계적 진화 실험',
            'initial_task': '''Python으로 StudentManager 클래스를 만드세요.

요구사항:
- 학생은 이름(name: str)과 ID(student_id: int)를 가집니다
- StudentManager는 다음 메서드를 가져야 합니다:
  * add_student(name, student_id): 학생 추가
  * get_student(student_id): 학생 조회
  * remove_student(student_id): 학생 삭제
- 간단한 사용 예제를 포함하세요''',

            'modifications': [
                '각 학생에게 점수 리스트(scores: List[int])를 추가하고, add_score(student_id, score)와 get_scores(student_id) 메서드를 구현하세요.',
                '각 학생의 평균 점수를 계산하는 get_average(student_id) 메서드와 평균에 따라 등급(A: 90+, B: 80+, C: 70+, D: 60+, F: 60미만)을 반환하는 get_grade(student_id) 메서드를 추가하세요.',
                'StudentManager의 모든 데이터를 JSON 파일로 저장하는 save_to_file(filename) 메서드와 로드하는 load_from_file(filename) 메서드를 추가하세요.',
                '모든 메서드에 타입 힌트를 추가하고, 적절한 예외 처리(학생을 찾을 수 없는 경우, 파일 I/O 오류 등)를 구현하여 코드를 리팩토링하세요.'
            ]
        }

    def run_pilot_experiment(self, num_repeats: int = 3) -> Dict[str, Any]:
        """파일럿 실험 실행"""
        results = {
            'scenario': self.scenario['name'],
            'baseline_results': [],
            'statedoc_results': []
        }

        print(f"\n🚀 파일럿 실험 시작")
        print(f"모델: {self.model}")
        print(f"반복 횟수: {num_repeats}")
        print(f"시나리오: {self.scenario['name']}")
        print("="*60)

        for repeat in range(num_repeats):
            print(f"\n📊 실험 {repeat + 1}/{num_repeats}")
            print("-"*40)

            # 베이스라인 에이전트 실행
            print("🔍 베이스라인 에이전트 실행 중...")
            baseline_agent = BaselineAgent(self.model, self.client)
            baseline_result = self._run_single_experiment(baseline_agent, "Baseline")
            results['baseline_results'].append(baseline_result)

            # StateDoc 에이전트 실행
            print("📋 StateDoc 에이전트 실행 중...")
            statedoc_agent = StateDocAgent(self.model, self.client)
            statedoc_result = self._run_single_experiment(statedoc_agent, "StateDoc")
            results['statedoc_results'].append(statedoc_result)

            # 중간 결과 출력
            print(f"   베이스라인 드리프트율: {baseline_result.drift_rate:.1%}")
            print(f"   StateDoc 드리프트율: {statedoc_result.drift_rate:.1%}")

            improvement = baseline_result.drift_rate - statedoc_result.drift_rate
            print(f"   개선 효과: {improvement:.1%}")

        return results

    def _run_single_experiment(self, agent, agent_type: str) -> ExperimentResult:
        """단일 에이전트로 실험 실행"""
        execution_times = []

        # 초기 코드 생성
        start_time = time.time()
        current_code = agent.solve_initial(self.scenario['initial_task'])
        execution_times.append(time.time() - start_time)

        # 초기 평가
        initial_score = self.evaluator.evaluate(current_code, self.scenario['initial_task'])
        scores = [initial_score]

        print(f"   → 초기 점수: {initial_score:.1f}/10")

        # 단계별 수정 및 평가
        for i, modification in enumerate(self.scenario['modifications'], 1):
            print(f"   → 수정 {i}/{len(self.scenario['modifications'])}: {modification[:50]}...")

            start_time = time.time()
            current_code = agent.modify_code(current_code, modification)
            execution_times.append(time.time() - start_time)

            score = self.evaluator.evaluate(current_code, modification)
            scores.append(score)

            print(f"      점수: {score:.1f}/10")

        # 드리프트율 계산
        drift_rate = self._calculate_drift_rate(scores)

        return ExperimentResult(
            agent_type=agent_type,
            scores=scores,
            drift_rate=drift_rate,
            execution_times=execution_times,
            interaction_log=agent.interaction_log
        )

    def _calculate_drift_rate(self, scores: List[float]) -> float:
        """의미 드리프트율 계산: (초기점수 - 최종점수) / 초기점수"""
        if len(scores) < 2 or scores[0] == 0:
            return 0.0

        drift = (scores[0] - scores[-1]) / scores[0]
        return max(0.0, drift)  # 음수는 0으로 처리 (성능이 향상된 경우)
