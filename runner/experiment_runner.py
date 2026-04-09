"""
experiment_runner.py — 실험 시나리오 실행 및 결과 수집

이 모듈이 실험의 핵심 루프를 담당합니다.

실험 구조:
  N번 반복 (--repeats)
    ├─ BaselineAgent 실행 → 초기 코드 생성 → 4번 수정 → 각 단계 채점
    └─ StateDocAgent 실행 → 초기 코드 생성 → 4번 수정 → 각 단계 채점

시나리오 (OrderSystem Evolution) — 충돌 유발형:
  초기: OrderManager 클래스 (add/get/cancel/list_order)
  수정1: Item dataclass 도입 → add_order 시그니처 변경, total 자동계산으로 전환
  수정2: 할인 시스템 → total 계산 로직 변경 (기존 자동계산 방식과 충돌)
  수정3: 상태 머신 → cancel_order 동작 변경 (단순 삭제 → 상태 전환)
  수정4: 결제 통합 → process_payment와 confirm_order 역할 충돌

수집하는 데이터:
  - 각 단계별 점수 (0~10)
  - 드리프트율 = (초기점수 - 최종점수) / 초기점수
  - 각 단계 실행 시간
  - LLM 호출 횟수 (interaction_log 길이)
"""
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Any
from agents import BaselineAgent, LayeredMemoryAgent, SemanticCompressorAgent, SemanticCompressorV2Agent, SemanticCompressorV3Agent
from evaluator import CodeEvaluator
from evaluator import CodeExecutor


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
    test_details: List[List[str]] = None  # 각 단계별 테스트 상세 결과 (exec 모드)
    verifier_log: List[Dict[str, Any]] = None  # V3 Verifier 판정 이력 (SemanticV3 전용)


class ExperimentRunner:
    """실험 실행 및 관리 클래스"""

    def __init__(self, model: str, client: Any, eval_mode: str = 'llm'):
        """
        Parameters
        ----------
        model     : Ollama 모델 이름
        client    : ollama.Client 인스턴스 (에이전트와 평가자가 공유)
        eval_mode : 평가 방식 선택
                    'llm'  — LLM이 코드를 읽고 0~10점 채점 (기존 방식, 주관적)
                    'exec' — 실제 Python 테스트를 실행해 통과율로 채점 (객관적)
        """
        self.model = model
        self.client = client
        self.eval_mode = eval_mode

        # LLM 평가자 (eval_mode='llm'일 때 사용)
        self.evaluator = CodeEvaluator(model=model, client=client)

        # 코드 실행 평가자 (eval_mode='exec'일 때 사용)
        self.executor = CodeExecutor(timeout=15)

        # OrderSystem 충돌 유발형 시나리오 정의
        # 각 수정 단계가 이전 단계의 구현 방식을 변경하도록 설계됨:
        #   수정1: Order 내부 데이터 구조 변경 (dict → Item 객체)
        #   수정2: total 계산 로직 변경 (할인 반영으로 기존 계산식 파괴)
        #   수정3: cancel_order 동작 변경 (상태 제약 추가로 기존 단순 삭제 불가)
        #   수정4: confirm_order와 process_payment 역할 충돌
        # StateDoc은 이 변경 이력을 추적해 기존 메서드를 올바르게 수정할 수 있지만,
        # Baseline은 이전 컨텍스트를 잃으면 기존 메서드를 그대로 두거나 잘못 변경할 가능성이 높다.
        # BudgetTracker 시나리오 — 설계 의도 보존 측정
        #
        # 핵심 불변식: "감사 추적(Audit Trail) — 거래 삭제/직접수정 불가"
        # - step0에서 명시, 이후 단계에서는 언급 안 함
        # - step4(수정기능), step5(아카이브)에서 불변식과 직접 충돌
        # - DRIFT_PROBE: 불변식이 step2~5에서 유지되는지 측정
        #
        # 이론적 근거:
        # - Gotel & Finkelstein (1994): requirements rationale 미추적 → 이후 위반
        # - Laban et al. (2505.06120): 앵커링 현상 — 초반 의도가 후반에 망각
        self.budget_scenario = {
            'name': 'BudgetTracker Intent',
            'description': '가계부 시스템 — 감사 추적 불변식 보존 측정',
            'initial_task': '''Python으로 세무 신고용 가계부 시스템을 만드세요.

[핵심 설계 원칙 — 감사 추적(Audit Trail)]
이 시스템은 법적 감사 기록으로 사용됩니다. 반드시 지켜야 합니다:
- 모든 거래는 한 번 기록되면 절대 삭제할 수 없습니다
- 거래 내용을 직접 수정하는 것도 불가합니다
- 잘못된 거래는 반드시 "취소 거래"를 새로 추가하는 방식으로만 정정합니다
- get_all_transactions()는 항상 취소된 거래를 포함한 전체 이력을 반환합니다

요구사항:
- Transaction 클래스: tx_id(int), description(str), amount(float), date(str) 필드
- BudgetTracker 클래스:
  * add_transaction(tx_id, description, amount, date): 거래 추가
  * get_transaction(tx_id): 거래 조회, 없으면 None 반환
  * cancel_transaction(tx_id): 취소 — 원본 삭제 금지, 취소 상태 표시 또는 취소 거래 추가
  * get_all_transactions(): 전체 거래 목록 반환 (취소 포함)
- 간단한 사용 예제를 포함하세요''',

            'modifications': [
                # step1: 카테고리 추가 — 충돌 없음, warm-up
                '''카테고리 분류 기능을 추가하세요.
- Transaction에 category(str, 기본값 "기타") 필드를 추가하세요
- add_transaction()에 category 파라미터를 추가하세요 (선택적, 기본값 "기타")
- BudgetTracker에 get_transactions_by_category(category: str) 메서드를 추가하세요
- 기존 add_transaction, get_transaction, cancel_transaction, get_all_transactions가 여전히 동작해야 합니다
- cancel_transaction은 여전히 원본을 삭제하지 않아야 합니다''',

                # step2: 월별 요약 — 충돌 없음, 취소 거래 포함 여부 간접 테스트
                '''월별 지출/수입 요약 기능을 추가하세요.
- BudgetTracker에 get_monthly_summary(year_month: str) 메서드를 추가하세요
  * year_month 형식: "YYYY-MM" (예: "2026-01")
  * 해당 월의 거래 합계(total 또는 net)를 반환합니다
  * 반환값은 dict({"total": float}) 또는 숫자(float) 중 편한 방식으로 구현하세요
- 기존 모든 기능이 동작해야 합니다
- 취소된 거래도 이력에 포함되어야 합니다 (get_all_transactions 기준)''',

                # step3: 예산 한도 — 약한 충돌 (한도 초과 거래 처리 방식)
                '''예산 한도 관리 기능을 추가하세요.
- BudgetTracker에 set_budget_limit(category: str, limit: float) 메서드를 추가하세요
- BudgetTracker에 get_budget_status(category: str) 메서드를 추가하세요
  * 해당 카테고리의 한도, 사용액, 잔여 한도를 반환합니다
- 한도를 초과하는 거래가 추가될 때는 거래를 기록하되 경고를 표시하거나 예외를 발생시켜도 됩니다
  (단, 기록 자체는 남아야 합니다 — 감사 추적 원칙)
- 기존 모든 기능이 동작해야 합니다''',

                # step4: 거래 수정 기능 — [강한 충돌] 불변식과 직접 충돌
                # 불변식을 기억하면: 원본 보존 + 수정본을 새 거래로 추가
                # 불변식을 잊으면: 기존 거래를 직접 덮어씀
                '''거래 수정 기능을 추가하세요.
- BudgetTracker에 update_transaction(tx_id, **kwargs) 메서드를 추가하세요
  * description, amount, category 등을 수정할 수 있어야 합니다
  * kwargs로 전달된 필드만 업데이트합니다
- 기존 get_monthly_summary, get_transactions_by_category, get_budget_status가 동작해야 합니다
- 기존 모든 기능이 동작해야 합니다''',

                # step5: 아카이브 기능 — [강한 충돌] "정리"는 삭제를 연상시킴
                # 불변식을 기억하면: 삭제 대신 아카이브(별도 저장소 이동)
                # 불변식을 잊으면: 실제 삭제 구현
                '''오래된 거래 아카이브 기능을 추가하세요.
- BudgetTracker에 archive_old_transactions(before_date: str) 메서드를 추가하세요
  * before_date 이전의 거래를 정리합니다
  * 정리된 거래는 별도 아카이브에 보관하고 활성 거래에서 분리합니다
- BudgetTracker에 get_archived_transactions() 메서드를 추가하세요
  * 아카이브된 거래 목록을 반환합니다
- 기존 update_transaction, cancel_transaction, get_all_transactions가 동작해야 합니다
- 기존 모든 기능이 동작해야 합니다''',
            ]
        }

        self.scenario = {
            'name': 'OrderSystem Evolution',
            'description': '주문 관리 시스템의 단계적 진화 — 충돌 유발형 시나리오',
            'initial_task': '''Python으로 주문 관리 시스템을 만드세요.

요구사항:
- Order 클래스: order_id(int), items(list of str), total(float) 필드를 가집니다
- OrderManager 클래스는 다음 메서드를 가져야 합니다:
  * add_order(order_id, items, total): 주문 추가
  * get_order(order_id): 주문 조회, 없으면 None 반환
  * cancel_order(order_id): 주문 취소(삭제)
  * list_orders(): 모든 주문 목록 반환
- 간단한 사용 예제를 포함하세요''',

            'modifications': [
                # 수정1: 아이템 데이터 구조 변경 — add_order 시그니처 변경 유발
                # items가 str 리스트에서 dict 리스트로 바뀌므로 add_order와 list_orders가 영향받음
                '''아이템을 더 구조화하세요.
- Item 클래스(또는 dataclass)를 추가하세요: name(str), price(float), quantity(int) 필드
- Order.items를 List[str] 대신 List[Item]으로 변경하세요
- add_order(order_id, items: List[Item], total: float)로 시그니처를 업데이트하세요
- Order.total은 items의 price * quantity 합계로 자동 계산되도록 변경하세요 (total 파라미터 제거)
- 기존 add_order, get_order, cancel_order, list_orders가 새 구조와 함께 정상 동작해야 합니다''',

                # 수정2: total 계산 로직 변경 — 할인 적용으로 기존 total 계산식 파괴
                # apply_discount를 OrderManager에 추가 (order_id로 조회 후 적용)
                # 할인율은 0.0~1.0 범위 (0.1 = 10%)
                '''할인 시스템을 추가하세요.
- Order에 discount_percent(float, 기본값 0.0) 필드를 추가하세요 (0.0~1.0 범위, 0.1 = 10%)
- OrderManager에 apply_discount(order_id, discount_percent) 메서드를 추가하세요
  * 해당 order_id의 Order를 찾아 discount_percent를 업데이트합니다
  * discount_percent는 0.0~1.0 범위입니다 (예: 0.1 = 10%, 0.2 = 20%)
- Order.total은 items 합계에서 discount_percent를 적용한 최종 금액이어야 합니다
  예) items 합계 20.0원, discount_percent=0.1(10%) → total = 18.0원
- OrderManager에 get_order_total(order_id) 메서드를 추가하세요: 현재 최종 금액 반환
- list_orders()가 각 주문의 할인 적용 후 total을 보여줘야 합니다
- 기존 add_order, cancel_order도 여전히 동작해야 합니다''',

                # 수정3: cancel_order 동작 변경 — 상태 머신 추가로 기존 단순 삭제 불가
                # 기존 cancel_order는 그냥 삭제했지만 이제 상태 확인 후 CANCELLED 상태로 전환
                '''주문 상태 관리를 추가하세요.
- Order에 status 필드 추가: "PENDING", "CONFIRMED", "SHIPPED", "CANCELLED" 중 하나
  (새 주문의 기본 status는 "PENDING")
- confirm_order(order_id): PENDING → CONFIRMED로 전환
- ship_order(order_id): CONFIRMED → SHIPPED로 전환
- cancel_order(order_id)를 다음과 같이 변경하세요:
  * 반드시 self.orders에서 주문을 삭제하지 말고 status만 "CANCELLED"로 변경하세요
  * PENDING 또는 CONFIRMED 상태일 때만 CANCELLED로 전환 가능합니다
  * SHIPPED 상태면 ValueError("배송 중인 주문은 취소할 수 없습니다")를 발생시키세요
  * 중요: del self.orders[order_id]를 절대 호출하지 마세요 — get_order로 취소된 주문을 조회할 수 있어야 합니다
- list_orders()가 status 정보를 포함해야 합니다
- get_order, apply_discount, get_order_total이 여전히 동작해야 합니다
- 사용 예제를 작성할 때 cancel_order 호출은 반드시 try/except ValueError로 감싸세요''',

                # 수정4: 결제 통합 — confirm_order와 process_payment 역할 충돌
                # process_payment 완료 시 자동 CONFIRMED 전환 → confirm_order와 역할 중복
                '''결제 시스템을 통합하세요.
- Payment 클래스(또는 dataclass): payment_id(int), order_id(int), amount(float), method(str) 필드
- OrderManager에 추가:
  * process_payment(order_id, amount, method): 결제 처리
    - amount가 Order의 최종 total과 일치해야 합니다 (불일치 시 ValueError)
    - 결제 성공 시 Order status를 자동으로 CONFIRMED로 변경합니다
    - Payment 객체를 내부에 저장하고 반환합니다
  * get_payment(order_id): 해당 주문의 결제 정보 반환
- confirm_order는 결제 없이 수동으로 확인하는 용도로 유지하세요
- 기존 ship_order, cancel_order, apply_discount, get_order_total이 모두 동작해야 합니다''',

                # 수정5: 재고 관리 — Item에 재고 개념 추가, add_order 시 재고 검사
                # Baseline: 수정1에서 만든 Item 구조 기억이 희미해질 수 있음
                '''재고 관리 시스템을 추가하세요.
- Item에 stock(int, 현재 재고 수량) 필드를 추가하세요
- Inventory 클래스를 추가하세요:
  * add_item(item_name, price, stock): 상품을 재고에 등록
  * get_stock(item_name): 현재 재고 수량 반환
  * reduce_stock(item_name, quantity): 재고 차감 (부족 시 ValueError)
- OrderManager.add_order() 호출 시 Inventory를 통해 재고를 자동으로 차감하세요
  * add_order(order_id, items: List[Item], inventory: Inventory)로 시그니처 변경
  * 재고 부족 시 ValueError("재고 부족: {item_name}") 발생
- 기존 get_order, cancel_order, list_orders, apply_discount, get_order_total,
  confirm_order, ship_order, process_payment, get_payment이 모두 동작해야 합니다''',

                # 수정6: 주문 이력 조회 — 취소된 주문 포함 전체 이력
                # Baseline: 수정3의 cancel_order 동작(삭제 금지)을 기억하는지 테스트
                '''주문 이력 관리 기능을 추가하세요.
- OrderManager에 get_order_history() 메서드를 추가하세요:
  * CANCELLED 포함 모든 주문을 반환합니다 (list_orders는 활성 주문만 반환)
  * 반환값은 Order 객체의 리스트여야 합니다 (튜플 리스트 아님)
  * 주문 생성 시각(created_at: datetime) 기준으로 정렬합니다
- Order에 created_at(datetime) 필드를 추가하세요 (add_order 시 자동 설정)
  * 중요: Python dataclass 필드 순서 규칙 — default 없는 필드가 앞에, default 있는 필드가 뒤에 와야 합니다.
    올바른 예: order_id: int, items: List[Item], discount_percent: float = 0.0, status: str = "PENDING", created_at: datetime = field(default_factory=datetime.now)
    또는 created_at을 __post_init__에서 설정하세요: self.created_at = datetime.now()
- OrderManager에 get_orders_by_status(status: str) 메서드를 추가하세요:
  * 지정한 status의 주문만 반환합니다 ("PENDING", "CONFIRMED", "SHIPPED", "CANCELLED")
- 기존 cancel_order가 주문을 삭제하지 않고 CANCELLED 상태로 유지해야 합니다
  (get_order_history에서 취소 주문이 조회되려면 반드시 보존되어야 합니다)
- 기존 모든 기능이 동작해야 합니다''',

            ]
        }
        # step7(환불), step8(멀티고객) 제거 — 드리프트는 step6에서 이미 포착됨
        # 스텝 축소로 실험 시간 ~40% 단축 (9스텝 → 7스텝)

    def run_quick_experiment(self, num_repeats: int = 3,
                             agents: List[str] = None,
                             start_step: int = 3) -> Dict[str, Any]:
        """
        빠른 검증 모드 — step0~(start_step-1)을 건너뛰고 start_step 이후만 실행.

        step0~3은 모든 에이전트가 거의 항상 10점이므로 생략 가능.
        이전 실험에서 저장된 step{start_step} 코드를 기준점으로 사용한다.

        Parameters
        ----------
        agents     : 실행할 에이전트 목록 (None이면 전체)
                     예: ["Baseline", "SemanticCompressorV2"]
        start_step : 시작 단계 (기본 3 — step3 코드부터 step4,5,6만 실행)
        """
        all_agents = {
            'Baseline':           lambda: BaselineAgent(self.model, self.client, max_tokens=4096),
            'LayeredMemory':      lambda: LayeredMemoryAgent(self.model, self.client, max_tokens=4096),
            'SemanticCompressor': lambda: SemanticCompressorAgent(self.model, self.client, max_tokens=4096),
            'SemanticCompressorV2': lambda: SemanticCompressorV2Agent(self.model, self.client, max_tokens=4096),
        }
        selected = agents or list(all_agents.keys())

        # start_step 코드 로드 — Baseline의 이전 실험 결과 사용
        # (step3까지는 모든 에이전트가 동일한 수준의 코드를 생성하므로 공유 기준점으로 사용)
        ref_dirs = [
            f"results/debug_baseline/step{start_step}_mod{start_step}.py",
            f"results/debug_layeredmemory/step{start_step}_mod{start_step}.py",
            f"results/debug_semanticcompressor/step{start_step}_mod{start_step}.py",
        ]
        start_code = None
        for path in ref_dirs:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    start_code = f.read()
                print(f"기준점 코드: {path}")
                break

        if not start_code:
            print(f"⚠️  step{start_step} 기준 코드를 찾을 수 없습니다. 전체 실험으로 전환합니다.")
            return self.run_pilot_experiment(num_repeats)

        modifications = self.scenario['modifications'][start_step:]
        results = {name: [] for name in selected}
        results['scenario'] = self.scenario['name']

        print(f"\n⚡ 빠른 실험 모드 (step{start_step}~{start_step + len(modifications)})")
        print(f"모델: {self.model} | 반복: {num_repeats} | 에이전트: {', '.join(selected)}")
        print("=" * 60)

        for repeat in range(num_repeats):
            print(f"\n📊 실험 {repeat + 1}/{num_repeats}")
            print("-" * 40)

            for name in selected:
                print(f"  [{name}] 실행 중...")
                agent = all_agents[name]()
                agent.solve_initial_from_code(start_code)
                result = self._run_quick_steps(agent, name, start_code,
                                               modifications, start_step)
                results[name].append(result)
                print(f"  → 드리프트: {result.drift_rate:.3f}점")

        # 호환성을 위해 기존 키 매핑
        return {
            'scenario': results['scenario'],
            'baseline_results':    results.get('Baseline', []),
            'statedoc_results':    results.get('LayeredMemory', []),
            'semantic_results':    results.get('SemanticCompressor', []),
            'semantic_v2_results': results.get('SemanticCompressorV2', []),
            '_quick_raw':          results,
        }

    def _run_quick_steps(self, agent, agent_type: str, start_code: str,
                         modifications: List[str], start_step: int) -> ExperimentResult:
        """start_code를 기준으로 수정 단계만 실행한다."""
        execution_times = []
        all_test_details = []
        debug_dir = f"results/debug_{agent_type.lower()}"
        os.makedirs(debug_dir, exist_ok=True)

        current_code = start_code
        # start_step 점수를 기준점으로 측정
        initial_score, initial_details = self._score(current_code, step_index=start_step)
        scores = [initial_score]
        all_test_details.append(initial_details)
        print(f"     step{start_step} 기준 점수: {initial_score:.1f}/10")

        for i, modification in enumerate(modifications, start_step + 1):
            print(f"     → 수정 {i}/{start_step + len(modifications)}: {modification[:50]}...")
            start_time = time.time()
            current_code = agent.modify_code_with_syntax_retry(current_code, modification)
            execution_times.append(time.time() - start_time)

            with open(f"{debug_dir}/step{i}_mod{i}.py", "w", encoding="utf-8") as f:
                f.write(current_code)

            score, step_details = self._score(current_code, step_index=i)
            scores.append(score)
            all_test_details.append(step_details)
            print(f"        점수: {score:.1f}/10")

        drift_rate = self._calculate_drift_rate(scores)
        return ExperimentResult(
            agent_type=agent_type,
            scores=scores,
            drift_rate=drift_rate,
            execution_times=execution_times,
            interaction_log=agent.interaction_log,
            test_details=all_test_details,
        )

    def run_budget_experiment(self, num_repeats: int = 3,
                              agents: List[str] = None) -> Dict[str, Any]:
        """
        BudgetTracker 시나리오 실험 — 설계 의도 보존 측정.

        핵심 측정: step4(수정기능), step5(아카이브)에서 감사 추적 불변식이 유지되는가?
        DRIFT_PROBE가 불변식 위반을 단계별로 측정함.
        """
        all_agents = {
            'Baseline':             lambda: BaselineAgent(self.model, self.client, max_tokens=4096),
            'SemanticCompressorV2': lambda: SemanticCompressorV2Agent(self.model, self.client, max_tokens=4096),
            'SemanticCompressorV3': lambda: SemanticCompressorV3Agent(self.model, self.client, max_tokens=4096),
        }
        selected = agents or list(all_agents.keys())

        results = {'scenario': self.budget_scenario['name']}
        for name in selected:
            results[name] = []

        print(f"\n🚀 BudgetTracker 실험 시작")
        print(f"모델: {self.model} | 반복: {num_repeats} | 에이전트: {', '.join(selected)}")
        print("="*60)

        for repeat in range(num_repeats):
            print(f"\n📊 실험 {repeat + 1}/{num_repeats}")
            print("-"*40)
            for name in selected:
                print(f"🔍 {name} 에이전트 실행 중...")
                agent = all_agents[name]()
                result = self._run_single_experiment(agent, name,
                                                     scenario=self.budget_scenario,
                                                     eval_budget=True)
                results[name].append(result)
                print(f"   → 드리프트: {result.drift_rate:.3f}점")

        return results

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
            'statedoc_results': [],
            'semantic_results': [],
            'semantic_v2_results': []
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
            baseline_agent = BaselineAgent(self.model, self.client, max_tokens=4096)
            baseline_result = self._run_single_experiment(baseline_agent, "Baseline")
            results['baseline_results'].append(baseline_result)

            print("🧩 LayeredMemory 에이전트 실행 중...")
            statedoc_agent = LayeredMemoryAgent(self.model, self.client, max_tokens=4096)
            statedoc_result = self._run_single_experiment(statedoc_agent, "LayeredMemory")
            results['statedoc_results'].append(statedoc_result)

            print("🔬 SemanticCompressor 에이전트 실행 중...")
            semantic_agent = SemanticCompressorAgent(self.model, self.client, max_tokens=4096)
            semantic_result = self._run_single_experiment(semantic_agent, "SemanticCompressor")
            results['semantic_results'].append(semantic_result)

            print("🔬 SemanticCompressorV2 에이전트 실행 중...")
            semantic_v2_agent = SemanticCompressorV2Agent(self.model, self.client, max_tokens=4096)
            semantic_v2_result = self._run_single_experiment(semantic_v2_agent, "SemanticCompressorV2")
            results['semantic_v2_results'].append(semantic_v2_result)

            # 중간 결과 출력
            print(f"   베이스라인 드리프트:         {baseline_result.drift_rate:.3f}점")
            print(f"   LayeredMemory 드리프트:      {statedoc_result.drift_rate:.3f}점")
            print(f"   SemanticCompressor 드리프트:  {semantic_result.drift_rate:.3f}점")
            print(f"   SemanticCompressorV2 드리프트: {semantic_v2_result.drift_rate:.3f}점")

        return results

    def _run_single_experiment(self, agent, agent_type: str,
                               scenario: dict = None,
                               eval_budget: bool = False) -> ExperimentResult:
        """
        단일 에이전트로 시나리오 전체(초기 + 수정 4회)를 실행합니다.

        흐름:
          1. solve_initial() → 초기 코드 생성 + 채점
          2. modify_code() × 4 → 수정 후 채점
          3. _calculate_drift_rate() → 점수 리스트로 드리프트율 계산
        """
        execution_times = []
        all_test_details = []  # 단계별 테스트 상세 결과

        # 실행할 시나리오 결정 (budget 또는 기본 OrderSystem)
        active_scenario = scenario if scenario is not None else self.scenario

        # 생성된 코드를 단계별로 저장할 디렉터리 (exec 모드에서 디버깅에 사용)
        debug_dir = f"results/debug_{agent_type.lower()}"
        os.makedirs(debug_dir, exist_ok=True)

        # 초기 코드 생성 및 시간 측정
        start_time = time.time()
        current_code = agent.solve_initial(active_scenario['initial_task'])
        execution_times.append(time.time() - start_time)

        # 단계 0 코드 저장
        with open(f"{debug_dir}/step0_initial.py", "w", encoding="utf-8") as f:
            f.write(current_code)

        # 누적 요구사항 추적 리스트
        completed_requirements = [active_scenario['initial_task']]

        # 초기 코드 채점 (기준점이 됨)
        initial_score, initial_details = self._score(current_code, step_index=0,
                                                     eval_budget=eval_budget)
        scores = [initial_score]
        all_test_details.append(initial_details)
        print(f"   → 초기 점수: {initial_score:.1f}/10")

        # 수정 단계 반복
        for i, modification in enumerate(active_scenario['modifications'], 1):
            print(f"   → 수정 {i}/{len(active_scenario['modifications'])}: {modification[:50]}...")

            start_time = time.time()
            current_code = agent.modify_code_with_syntax_retry(current_code, modification)
            execution_times.append(time.time() - start_time)

            # 단계별 코드 저장 — 테스트 실패 시 직접 열어서 원인 확인 가능
            with open(f"{debug_dir}/step{i}_mod{i}.py", "w", encoding="utf-8") as f:
                f.write(current_code)

            # 이번 수정 요청을 누적 목록에 추가
            completed_requirements.append(modification)

            score, step_details = self._score(current_code, step_index=i,
                                              completed_requirements=completed_requirements,
                                              eval_budget=eval_budget)
            scores.append(score)
            all_test_details.append(step_details)
            print(f"      점수: {score:.1f}/10")

        # 최종 드리프트율 계산
        drift_rate = self._calculate_drift_rate(scores)

        # V3 에이전트인 경우 Verifier 판정 이력 수집
        verifier_log = getattr(agent, 'verifier_log', None)

        return ExperimentResult(
            agent_type=agent_type,
            scores=scores,                        # [초기, 수정1, 수정2, 수정3, 수정4]
            drift_rate=drift_rate,
            execution_times=execution_times,      # [초기시간, 수정1시간, ...]
            interaction_log=agent.interaction_log,# LLM 호출 기록 전체
            test_details=all_test_details,        # 단계별 테스트 상세 결과 (DRIFT_PROBE 포함)
            verifier_log=verifier_log,            # Verifier 판정 이력 (V3 전용)
        )

    def _score(self, code: str, step_index: int,
               completed_requirements: List[str] = None,
               eval_budget: bool = False) -> float:
        """
        eval_mode에 따라 코드를 채점합니다.

        'exec' 모드: CodeExecutor로 실제 Python 테스트 실행 → 통과율 × 10
        'llm'  모드: CodeEvaluator로 LLM이 누적 요구사항을 기준으로 채점
        eval_budget=True: BudgetTracker 시나리오 테스트 사용
        """
        if self.eval_mode == 'exec':
            if eval_budget:
                score, details = self.executor.evaluate_budget(code, step_index)
            else:
                score, details = self.executor.evaluate(code, step_index)
            for d in details:
                pass_mark = "✓" if d.startswith("TEST PASS") else "✗"
                print(f"         {pass_mark} {d}")
            return score, details
        else:
            # LLM 평가: 누적 요구사항 텍스트 생성
            if completed_requirements is None:
                completed_requirements = [self.scenario['initial_task']]
            cumulative = "\n\n".join(
                f"[요구사항 {j}]\n{req}"
                for j, req in enumerate(completed_requirements)
            )
            return self.evaluator.evaluate(code, cumulative), []

    def _calculate_drift_rate(self, scores: List[float]) -> float:
        """
        점수 리스트로 의미 드리프트 절대 하락량을 계산합니다.

        공식: 초기점수 - 최솟값  (0~10 척도 위의 절대 점수 하락)

        비율(%) 대신 절대량을 사용하는 이유:
          비율 공식 (초기 - 최솟값) / 초기 는 초기 점수가 높을수록 분모가 커져
          동일한 0.5점 하락도 초기 점수에 따라 다르게 측정됩니다.
            초기 9.5 → 9.0: 0.5 / 9.5 = 5.26%
            초기 9.0 → 8.5: 0.5 / 9.0 = 5.56%
          초기에 더 좋은 코드를 만든 에이전트가 불리해지는 왜곡이 발생합니다.

          절대량 공식은 0.5점 하락을 항상 0.5로 처리합니다.
          두 에이전트의 초기 점수가 달라도 공정하게 비교할 수 있습니다.

        예시:
          [9.5, 9.0, 9.5, 9.5, 9.5] → 9.5 - 9.0 = 0.5 (중간 하락 포착)
          [9.0, 9.0, 9.0, 9.0, 9.2] → 9.0 - 9.0 = 0.0 (하락 없음)
          [9.0, 9.0, 9.0, 8.5, 9.2] → 9.0 - 8.5 = 0.5 (중간 하락 포착)
          [8.0, 8.5, 9.0, 9.0, 9.0] → 8.0 - 8.0 = 0.0 (초기가 최솟값, 계속 향상)
        """
        if len(scores) < 2:
            return 0.0

        # 전체 구간에서 가장 낮은 점수와 초기 점수의 차이
        drift = scores[0] - min(scores)
        # 초기가 최솟값보다 낮은 경우(계속 향상)는 드리프트 없음
        return max(0.0, drift)
