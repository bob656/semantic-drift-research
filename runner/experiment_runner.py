"""
experiment_runner.py — 실험 시나리오 실행 및 결과 수집

이 모듈이 실험의 핵심 루프를 담당합니다.

실험 구조:
  N번 반복 (--repeats)
    ├─ BaselineAgent 실행 → 초기 코드 생성 → 4번 수정 → 각 단계 채점
    └─ StateDocAgent 실행 → 초기 코드 생성 → 4번 수정 → 각 단계 채점

시나리오 (StudentManager Evolution):
  초기: StudentManager 클래스 (add/get/remove_student)
  수정1: 점수 리스트 추가
  수정2: 평균/등급 계산 추가
  수정3: 파일 저장/로드 추가
  수정4: 타입 힌트 + 예외 처리 리팩토링

수집하는 데이터:
  - 각 단계별 점수 (0~10)
  - 드리프트율 = (초기점수 - 최종점수) / 초기점수
  - 각 단계 실행 시간
  - LLM 호출 횟수 (interaction_log 길이)
"""
import time
from dataclasses import dataclass
from typing import List, Dict, Any
from agents import BaselineAgent, StateDocAgent
from evaluator import CodeEvaluator


@dataclass
class ExperimentResult:
    """
    단일 에이전트의 1회 실험 결과를 담는 데이터 클래스.

    Attributes
    ----------
    agent_type      : "Baseline" 또는 "StateDoc"
    scores          : 각 단계별 점수 리스트 [초기, 수정1, 수정2, 수정3, 수정4]
    drift_rate      : (초기점수 - 최종점수) / 초기점수  (0.0 이상, 클수록 품질 하락)
    execution_times : 각 단계에서 LLM 응답까지 걸린 시간(초) 리스트
    interaction_log : base_agent.py의 call_llm()이 기록한 모든 호출 내역
    """
    agent_type: str
    scores: List[float]
    drift_rate: float
    execution_times: List[float]
    interaction_log: List[Dict[str, Any]]


class ExperimentRunner:
    """실험 실행 및 관리 클래스"""

    def __init__(self, model: str, client: Any):
        """
        Parameters
        ----------
        model  : Ollama 모델 이름
        client : ollama.Client 인스턴스 (에이전트와 평가자가 공유)
        """
        self.model = model
        self.client = client

        # 에이전트가 생성한 코드를 채점하는 평가자
        # 에이전트와 동일한 모델/클라이언트를 사용합니다
        self.evaluator = CodeEvaluator(model=model, client=client)

        # StudentManager 진화 시나리오 정의
        # 초기 과제 1개 + 순서대로 적용할 수정 요청 4개
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
                # 수정1: 데이터 구조 변경 + 메서드 2개 추가
                '각 학생에게 점수 리스트(scores: List[int])를 추가하고, add_score(student_id, score)와 get_scores(student_id) 메서드를 구현하세요.',
                # 수정2: 계산 메서드 추가
                '각 학생의 평균 점수를 계산하는 get_average(student_id) 메서드와 평균에 따라 등급(A: 90+, B: 80+, C: 70+, D: 60+, F: 60미만)을 반환하는 get_grade(student_id) 메서드를 추가하세요.',
                # 수정3: I/O 기능 추가
                'StudentManager의 모든 데이터를 JSON 파일로 저장하는 save_to_file(filename) 메서드와 로드하는 load_from_file(filename) 메서드를 추가하세요.',
                # 수정4: 기능 추가 없이 리팩토링만 — 드리프트 유발 가능성 높음
                '모든 메서드에 타입 힌트를 추가하고, 적절한 예외 처리(학생을 찾을 수 없는 경우, 파일 I/O 오류 등)를 구현하여 코드를 리팩토링하세요.'
            ]
        }

    def run_pilot_experiment(self, num_repeats: int = 3) -> Dict[str, Any]:
        """
        파일럿 실험을 num_repeats회 반복 실행합니다.

        매 반복마다 Baseline과 StateDoc을 모두 실행하여
        동일 조건에서 비교할 수 있도록 합니다.

        Returns
        -------
        dict : {
            'scenario': 시나리오 이름,
            'baseline_results': [ExperimentResult, ...],
            'statedoc_results':  [ExperimentResult, ...]
        }
        """
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

            # 각 반복마다 에이전트를 새로 생성 → 이전 실험의 상태가 남지 않음
            print("🔍 베이스라인 에이전트 실행 중...")
            baseline_agent = BaselineAgent(self.model, self.client)
            baseline_result = self._run_single_experiment(baseline_agent, "Baseline")
            results['baseline_results'].append(baseline_result)

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
        """
        단일 에이전트로 시나리오 전체(초기 + 수정 4회)를 실행합니다.

        흐름:
          1. solve_initial() → 초기 코드 생성 + 채점
          2. modify_code() × 4 → 수정 후 채점
          3. _calculate_drift_rate() → 점수 리스트로 드리프트율 계산
        """
        execution_times = []

        # 초기 코드 생성 및 시간 측정
        start_time = time.time()
        current_code = agent.solve_initial(self.scenario['initial_task'])
        execution_times.append(time.time() - start_time)

        # 초기 코드 채점 (기준점이 됨 — 드리프트율 계산의 분모)
        initial_score = self.evaluator.evaluate(current_code, self.scenario['initial_task'])
        scores = [initial_score]
        print(f"   → 초기 점수: {initial_score:.1f}/10")

        # 수정 단계 반복
        for i, modification in enumerate(self.scenario['modifications'], 1):
            print(f"   → 수정 {i}/{len(self.scenario['modifications'])}: {modification[:50]}...")

            start_time = time.time()
            # 에이전트가 현재 코드를 받아 수정 요청을 반영한 새 코드를 반환
            current_code = agent.modify_code(current_code, modification)
            execution_times.append(time.time() - start_time)

            # 주의: 평가 기준이 'modification'(해당 단계 요청)만임
            # 이전 단계 기능 보존 여부를 체크하지 않는 구조적 한계 존재
            score = self.evaluator.evaluate(current_code, modification)
            scores.append(score)
            print(f"      점수: {score:.1f}/10")

        # 최종 드리프트율 계산
        drift_rate = self._calculate_drift_rate(scores)

        return ExperimentResult(
            agent_type=agent_type,
            scores=scores,                        # [초기, 수정1, 수정2, 수정3, 수정4]
            drift_rate=drift_rate,
            execution_times=execution_times,      # [초기시간, 수정1시간, ...]
            interaction_log=agent.interaction_log # LLM 호출 기록 전체
        )

    def _calculate_drift_rate(self, scores: List[float]) -> float:
        """
        점수 리스트로 의미 드리프트율을 계산합니다.

        공식: (초기점수 - 최종점수) / 초기점수

        예시:
          초기 8.5, 최종 8.0 → (8.5 - 8.0) / 8.5 = 0.059 (5.9%)
          초기 8.0, 최종 8.5 → 음수 → 0.0으로 처리 (성능 향상은 드리프트 아님)

        주의:
          최초 점수(scores[0])와 최종 점수(scores[-1])만 비교합니다.
          중간 단계에서 점수가 떨어졌다가 회복된 경우는 드리프트 0으로 처리됩니다.
        """
        if len(scores) < 2 or scores[0] == 0:
            return 0.0

        drift = (scores[0] - scores[-1]) / scores[0]
        # 음수(성능 향상)는 드리프트가 아니므로 0으로 클리핑
        return max(0.0, drift)
