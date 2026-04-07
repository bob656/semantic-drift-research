"""
diagnose_step6.py — step6 붕괴 원인 진단

가설 검증:
  H1 (생성 능력 한계): step5 완성 코드를 직접 주고 step6만 요청해도 실패한다
  H2 (메모리/컨텍스트 오염): step5 완성 코드를 직접 주면 성공한다

실험:
  - 이전 실험에서 검증된 step5 코드를 그대로 사용
  - 3개 에이전트 모두에게 step6 요청만 전달
  - step6 테스트로 채점

결론 기준:
  점수 >= 7.0  →  H2 지지 (메모리 문제)  →  에이전트 설계가 유효
  점수  < 7.0  →  H1 지지 (생성 능력)   →  에이전트 전략 재검토 필요
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ollama import Client
from agents import BaselineAgent, LayeredMemoryAgent, SemanticCompressorAgent
from evaluator import CodeExecutor

# ── 설정 ────────────────────────────────────────────────────────────────────
HOST  = "http://192.168.100.52:11434"
MODEL = "qwen2.5-coder:14b"

STEP6_REQUEST = '''주문 이력 관리 기능을 추가하세요.
- OrderManager에 get_order_history() 메서드를 추가하세요:
  * CANCELLED 포함 모든 주문을 반환합니다 (list_orders는 활성 주문만 반환)
  * 주문 생성 시각(created_at: datetime) 기준으로 정렬합니다
- Order에 created_at(datetime) 필드를 추가하세요 (add_order 시 자동 설정)
- OrderManager에 get_orders_by_status(status: str) 메서드를 추가하세요:
  * 지정한 status의 주문만 반환합니다 ("PENDING", "CONFIRMED", "SHIPPED", "CANCELLED")
- 기존 cancel_order가 주문을 삭제하지 않고 CANCELLED 상태로 유지해야 합니다
  (get_order_history에서 취소 주문이 조회되려면 반드시 보존되어야 합니다)
- 기존 모든 기능이 동작해야 합니다'''

# ── step5 완성 코드 (이전 실험에서 LayeredMemory가 생성한 검증된 코드) ────────
STEP5_CODE = open(
    os.path.join(os.path.dirname(__file__),
                 "results/debug_layeredmemory/step5_mod5.py"),
    encoding="utf-8"
).read()


def run_diagnosis():
    print("=" * 60)
    print("step6 붕괴 원인 진단")
    print("=" * 60)
    print(f"모델: {MODEL}")
    print(f"step5 코드 길이: {len(STEP5_CODE)}자")
    print()

    client = Client(host=HOST, timeout=600)
    executor = CodeExecutor(timeout=15)

    agents = [
        ("Baseline",          BaselineAgent(MODEL, client, max_tokens=4096)),
        ("LayeredMemory",     LayeredMemoryAgent(MODEL, client, max_tokens=4096)),
        ("SemanticCompressor", SemanticCompressorAgent(MODEL, client, max_tokens=4096)),
    ]

    results = {}

    for name, agent in agents:
        print(f"── {name} ──────────────────────────────")

        # LayeredMemory / SemanticCompressor는 solve_initial에서 permanent_interface를
        # 설정하므로, step5 코드를 그대로 넘겨 내부 상태를 초기화한다.
        # (LLM 호출 없이 코드만 파싱하므로 시간/비용 최소화)
        agent.solve_initial_from_code(STEP5_CODE)

        print("  step6 수정 요청 중...")
        modified_code = agent.modify_code(STEP5_CODE, STEP6_REQUEST)

        score, details = executor.evaluate(modified_code, step_index=6)
        print(f"  점수: {score:.2f}/10")
        for d in details:
            mark = "✓" if d.startswith("TEST PASS") else "✗"
            print(f"    {mark} {d}")

        # DRIFT_PROBE 별도 집계
        probe_pass = sum(1 for d in details if d.startswith("TEST PASS") and "DRIFT_PROBE" in d)
        probe_total = sum(1 for d in details if "DRIFT_PROBE" in d)
        if probe_total > 0:
            print(f"  DRIFT_PROBE: {probe_pass}/{probe_total} 통과")

        results[name] = {"score": score, "details": details}
        print()

    # ── 결론 ────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("진단 결론")
    print("=" * 60)
    scores = [results[n]["score"] for n in results]
    avg = sum(scores) / len(scores)
    print(f"평균 점수: {avg:.2f}/10")
    print()

    if avg >= 7.0:
        print("→ H2 지지: 컨텍스트 오염 문제")
        print("  step5 코드를 직접 주면 step6를 풀 수 있음")
        print("  즉, 7단계 누적 대화에서 컨텍스트가 오염되어 실패하는 것")
        print("  에이전트 메모리 전략이 이 오염을 줄일 수 있는지가 핵심 연구 질문")
    elif avg >= 4.0:
        print("→ 혼합: 일부 생성 능력 한계 + 일부 컨텍스트 문제")
        print("  에이전트별 점수 차이를 확인하세요")
    else:
        print("→ H1 지지: 생성 능력 한계")
        print("  step5 코드를 직접 줘도 step6를 풀지 못함")
        print("  메모리 전략과 무관하게 모델 자체의 한계")
        print("  → 시나리오 단순화 또는 모델 교체 필요")

    print()
    for name, r in results.items():
        verdict = "생성능력OK" if r["score"] >= 7.0 else "생성능력부족"
        print(f"  {name}: {r['score']:.2f}/10  [{verdict}]")


if __name__ == "__main__":
    run_diagnosis()
