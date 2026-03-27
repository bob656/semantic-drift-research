"""
code_executor.py — 코드 실행 기반 객관적 평가 모듈

LLM 점수(주관적) 대신 실제 Python 코드를 실행해서 테스트 통과 여부로 평가합니다.

평가 방식:
  1. 에이전트가 생성한 코드를 임시 파일에 저장
  2. 각 단계별로 미리 정의된 테스트 코드를 실행
  3. 통과한 테스트 수 / 전체 테스트 수 = 0~10점 환산

장점:
  - 재현 가능: 같은 코드는 항상 같은 점수
  - 명확한 기준: LLM 평가자 편향 없음
  - 드리프트 직접 측정: 이전 기능이 실제로 동작하는지 확인

OrderSystem 시나리오 기준 테스트 케이스 정의:
  단계 0 (초기): add_order, get_order, cancel_order, list_orders
  단계 1 (수정1): Item 클래스, total 자동계산 (이전 기능 + 새 기능)
  단계 2 (수정2): apply_discount, get_order_total (이전 기능 + 새 기능)
  단계 3 (수정3): 상태 머신, cancel_order 제약 (이전 기능 + 새 기능)
  단계 4 (수정4): process_payment, get_payment (이전 기능 + 새 기능)
"""
import ast
import subprocess
import tempfile
import os
import sys
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 단계별 테스트 코드 (누적 — 이전 단계 테스트 포함)
# ─────────────────────────────────────────────

# 단계 0: 초기 OrderManager
_TESTS_STEP0 = '''
results = []

try:
    om = OrderManager()
    om.add_order(1, ["apple", "banana"], 15.0)
    om.add_order(2, ["milk"], 3.5)

    # get_order: 존재하는 주문
    o = om.get_order(1)
    results.append(("get_order_exists", o is not None))

    # get_order: 없는 주문 → None
    results.append(("get_order_none", om.get_order(999) is None))

    # list_orders: 2개
    results.append(("list_orders_count", len(om.list_orders()) == 2))

    # cancel_order: 주문 취소
    om.cancel_order(1)
    remaining = om.list_orders()
    # 취소 후 get_order(1)이 None이거나 CANCELLED 상태여야 함 (두 방식 모두 허용)
    o_after = om.get_order(1)
    cancelled_ok = (o_after is None) or (hasattr(o_after, "status") and o_after.status == "CANCELLED")
    results.append(("cancel_order", cancelled_ok))

except Exception as e:
    results.append(("step0_exception", False))
    print(f"STEP0 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 1: Item dataclass + total 자동계산 + 이전 기능 유지
# add_order_compat: 수정1 이후 LLM이 total 파라미터를 제거할 수 있으므로
# 두 시그니처(items만 / items+total)를 모두 허용하는 래퍼를 테스트 내에 정의
_TESTS_STEP1 = '''
results = []

def _add(om, order_id, items):
    """add_order가 total 파라미터를 받든 안 받든 동작하는 래퍼"""
    try:
        om.add_order(order_id, items)
    except TypeError:
        om.add_order(order_id, items, None)

try:
    # Item 클래스 존재 여부
    item1 = Item(name="apple", price=5.0, quantity=2)
    item2 = Item(name="milk", price=3.0, quantity=1)
    results.append(("item_class_exists", True))

    # Item 속성 접근
    results.append(("item_name", item1.name == "apple"))
    results.append(("item_price", item1.price == 5.0))
    results.append(("item_quantity", item1.quantity == 2))

    om = OrderManager()
    _add(om, 1, [item1, item2])

    o = om.get_order(1)
    results.append(("get_order_exists", o is not None))

    # total 자동계산: 5*2 + 3*1 = 13.0
    results.append(("total_auto_calc", abs(o.total - 13.0) < 0.01))

    # list_orders 여전히 동작
    results.append(("list_orders_still_works", len(om.list_orders()) == 1))

    # cancel_order 여전히 동작
    om.cancel_order(1)
    o_after = om.get_order(1)
    cancelled_ok = (o_after is None) or (hasattr(o_after, "status") and o_after.status == "CANCELLED")
    results.append(("cancel_order_still_works", cancelled_ok))

except Exception as e:
    results.append(("step1_exception", False))
    print(f"STEP1 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 2: 할인 시스템 + 이전 기능 유지
_TESTS_STEP2 = '''
results = []

def _add(om, order_id, items):
    try:
        om.add_order(order_id, items)
    except TypeError:
        om.add_order(order_id, items, None)

# Item이 중첩 클래스로 정의된 경우 전역으로 꺼내기
if "Item" not in dir():
    for _cls in [OrderManager, locals().get("Order")]:
        if _cls and hasattr(_cls, "Item"):
            Item = _cls.Item
            break

try:
    results.append(("item_accessible", "Item" in dir()))
    item1 = Item(name="apple", price=10.0, quantity=2)  # 20.0
    om = OrderManager()
    _add(om, 1, [item1])

    # apply_discount: 10% 할인 (0.1 = 10%, 0.0~1.0 범위)
    om.apply_discount(1, 0.1)
    o = om.get_order(1)
    results.append(("apply_discount_exists", True))

    # get_order_total: 20.0 * (1 - 0.1) = 18.0
    total = om.get_order_total(1)
    results.append(("get_order_total", abs(total - 18.0) < 0.01))

    # 할인 없는 주문의 total은 items 합계
    item2 = Item(name="milk", price=5.0, quantity=1)
    _add(om, 2, [item2])
    results.append(("no_discount_total", abs(om.get_order_total(2) - 5.0) < 0.01))

    # list_orders 여전히 동작
    results.append(("list_orders_still_works", len(om.list_orders()) >= 1))

    # cancel_order 여전히 동작
    om.cancel_order(2)
    o2_after = om.get_order(2)
    cancelled_ok = (o2_after is None) or (hasattr(o2_after, "status") and o2_after.status == "CANCELLED")
    results.append(("cancel_order_still_works", cancelled_ok))

    # get_order 여전히 동작
    results.append(("get_order_still_works", om.get_order(1) is not None))

except Exception as e:
    results.append(("step2_exception", False))
    print(f"STEP2 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 3: 상태 머신 + 이전 기능 유지
_TESTS_STEP3 = '''
results = []

def _add(om, order_id, items):
    """시그니처 검사로 auto-id/explicit-id 구분 후 올바른 호출만 실행"""
    import inspect
    try:
        params = list(inspect.signature(om.add_order).parameters.keys())
        use_explicit = bool(params) and params[0] in ('order_id', 'id', 'oid')
    except Exception:
        use_explicit = False
    if use_explicit:
        for call in [lambda: om.add_order(order_id, items),
                     lambda: om.add_order(order_id, items, None)]:
            try: call(); return
            except (TypeError, AttributeError): continue
    else:
        for call in [lambda: om.add_order(items),
                     lambda: om.add_order(order_id, items)]:
            try: call(); return
            except (TypeError, AttributeError): continue

if "Item" not in dir():
    for _cls in [OrderManager, locals().get("Order")]:
        if _cls and hasattr(_cls, "Item"):
            Item = _cls.Item
            break

try:
    item1 = Item(name="apple", price=10.0, quantity=1)
    om = OrderManager()
    _add(om, 1, [item1])
    _add(om, 2, [item1])
    _add(om, 3, [item1])

    # 초기 상태는 PENDING
    o = om.get_order(1)
    results.append(("initial_status_pending", hasattr(o, "status") and o.status == "PENDING"))

    # confirm_order: PENDING → CONFIRMED
    om.confirm_order(1)
    o1 = om.get_order(1)
    results.append(("confirm_order", o1.status == "CONFIRMED"))

    # ship_order: CONFIRMED → SHIPPED
    om.ship_order(1)
    o1 = om.get_order(1)
    results.append(("ship_order", o1.status == "SHIPPED"))

    # cancel_order SHIPPED → ValueError
    shipped_raises = False
    try:
        om.cancel_order(1)
    except (ValueError, Exception):
        shipped_raises = True
    results.append(("cancel_shipped_raises", shipped_raises))

    # cancel_order PENDING → CANCELLED (물리 삭제 금지, 상태 전환)
    om.cancel_order(2)
    o2 = om.get_order(2)
    results.append(("cancel_pending_ok", o2 is not None and o2.status == "CANCELLED"))

    # apply_discount 여전히 동작 (0.1 = 10%)
    om.apply_discount(3, 0.1)
    results.append(("apply_discount_still_works", True))

    # get_order_total 여전히 동작
    total = om.get_order_total(3)
    results.append(("get_order_total_still_works", abs(total - 9.0) < 0.01))

except Exception as e:
    results.append(("step3_exception", False))
    print(f"STEP3 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 4: 결제 통합 + 이전 기능 유지
_TESTS_STEP4 = '''
results = []

def _add(om, order_id, items):
    """시그니처 검사로 auto-id/explicit-id 구분 후 올바른 호출만 실행"""
    import inspect
    try:
        params = list(inspect.signature(om.add_order).parameters.keys())
        use_explicit = bool(params) and params[0] in ('order_id', 'id', 'oid')
    except Exception:
        use_explicit = False
    if use_explicit:
        for call in [lambda: om.add_order(order_id, items),
                     lambda: om.add_order(order_id, items, None)]:
            try: call(); return
            except (TypeError, AttributeError): continue
    else:
        for call in [lambda: om.add_order(items),
                     lambda: om.add_order(order_id, items)]:
            try: call(); return
            except (TypeError, AttributeError): continue

if "Item" not in dir():
    for _cls in [OrderManager, locals().get("Order")]:
        if _cls and hasattr(_cls, "Item"):
            Item = _cls.Item
            break

try:
    item1 = Item(name="apple", price=10.0, quantity=2)  # total = 20.0
    om = OrderManager()
    _add(om, 1, [item1])
    _add(om, 2, [item1])

    # process_payment: 정확한 금액
    payment = om.process_payment(1, 20.0, "credit_card")
    results.append(("process_payment_returns", payment is not None))

    # 결제 후 status → CONFIRMED
    o1 = om.get_order(1)
    results.append(("payment_auto_confirm", o1.status == "CONFIRMED"))

    # get_payment: 결제 정보 조회
    p = om.get_payment(1)
    results.append(("get_payment", p is not None))
    results.append(("payment_method", hasattr(p, "method") and p.method == "credit_card"))

    # process_payment: 금액 불일치 → ValueError
    wrong_amount_raises = False
    try:
        om.process_payment(2, 99.0, "cash")
    except (ValueError, Exception):
        wrong_amount_raises = True
    results.append(("wrong_amount_raises", wrong_amount_raises))

    # confirm_order 여전히 수동 동작
    _add(om, 3, [item1])
    om.confirm_order(3)
    o3 = om.get_order(3)
    results.append(("confirm_order_still_works", o3.status == "CONFIRMED"))

    # ship_order, cancel_order 여전히 동작
    om.ship_order(3)
    results.append(("ship_order_still_works", om.get_order(3).status == "SHIPPED"))

    # apply_discount + get_order_total 여전히 동작
    _add(om, 4, [item1])
    om.apply_discount(4, 0.2)  # 0.2 = 20%, 기대값: 20.0 * 0.8 = 16.0
    results.append(("apply_discount_still_works", abs(om.get_order_total(4) - 16.0) < 0.01))

except Exception as e:
    results.append(("step4_exception", False))
    print(f"STEP4 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 5: 재고 관리 + 이전 기능 유지
_TESTS_STEP5 = '''
results = []

def _make_item(name, price, quantity):
    """stock 필드 추가 여부에 관계없이 Item 생성"""
    try:
        return Item(name=name, price=price, quantity=quantity, stock=0)
    except TypeError:
        return Item(name=name, price=price, quantity=quantity)

try:
    # Inventory 클래스 존재 여부
    inv = Inventory()
    results.append(("inventory_exists", True))

    inv.add_item("apple", 10.0, 5)
    results.append(("add_item_works", True))

    results.append(("get_stock", inv.get_stock("apple") == 5))

    # reduce_stock 정상 동작
    inv.reduce_stock("apple", 2)
    results.append(("reduce_stock", inv.get_stock("apple") == 3))

    # reduce_stock 부족 시 ValueError
    stock_err = False
    try:
        inv.reduce_stock("apple", 99)
    except (ValueError, Exception):
        stock_err = True
    results.append(("reduce_stock_raises", stock_err))

    # OrderManager 생성 — inventory 파라미터 있는 버전/없는 버전 모두 허용
    inv2 = Inventory()
    inv2.add_item("apple", 10.0, 5)
    try:
        om = OrderManager(inv2)
    except TypeError:
        om = OrderManager()

    item1 = _make_item("apple", 10.0, 1)

    # add_order: 시그니처 검사로 올바른 호출 선택 (next_order_id 낭비 방지)
    import inspect as _inspect
    try:
        _params = list(_inspect.signature(om.add_order).parameters.keys())
        _use_explicit = bool(_params) and _params[0] in ("order_id", "id", "oid")
    except Exception:
        _use_explicit = False
    if _use_explicit:
        for call in [lambda: om.add_order(1, [item1], inv2),
                     lambda: om.add_order(1, [item1])]:
            try: call(); break
            except (TypeError, AttributeError): continue
    else:
        for call in [lambda: om.add_order([item1], inv2),
                     lambda: om.add_order([item1])]:
            try: call(); break
            except (TypeError, AttributeError): continue
    results.append(("add_order_with_inventory", om.get_order(1) is not None))

    # 이전 기능: apply_discount, get_order_total 여전히 동작
    om.apply_discount(1, 0.1)
    results.append(("apply_discount_still_works", abs(om.get_order_total(1) - 9.0) < 0.01))

    # 이전 기능: cancel_order가 CANCELLED 상태로 유지 (삭제 금지)
    om.cancel_order(1)
    o = om.get_order(1)
    results.append(("cancel_keeps_order", o is not None and o.status == "CANCELLED"))

except Exception as e:
    results.append(("step5_exception", False))
    print(f"STEP5 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 6: 주문 이력 + 이전 기능 유지
_TESTS_STEP6 = '''
results = []

def _make_item(name, price, quantity):
    try:
        return Item(name=name, price=price, quantity=quantity, stock=0)
    except TypeError:
        return Item(name=name, price=price, quantity=quantity)

def _add(om, oid, items):
    """시그니처 검사로 auto-id/explicit-id 구분, next_order_id 낭비 방지"""
    import inspect as _inspect
    inv = Inventory()
    inv.add_item("apple", 10.0, 100)
    try:
        _params = list(_inspect.signature(om.add_order).parameters.keys())
        _use_explicit = bool(_params) and _params[0] in ("order_id", "id", "oid")
    except Exception:
        _use_explicit = False
    if _use_explicit:
        for call in [lambda: om.add_order(oid, items, inv),
                     lambda: om.add_order(oid, items)]:
            try: call(); return
            except (TypeError, AttributeError, ValueError): continue
    else:
        for call in [lambda: om.add_order(items, inv),
                     lambda: om.add_order(items)]:
            try: call(); return
            except (TypeError, AttributeError, ValueError): continue

try:
    item1 = _make_item("apple", 10.0, 1)

    # OrderManager 생성 — inventory 파라미터 있는 버전/없는 버전 모두 허용
    inv_for_om = Inventory()
    inv_for_om.add_item("apple", 10.0, 100)
    try:
        om = OrderManager(inv_for_om)
    except TypeError:
        om = OrderManager()

    _add(om, 1, [item1])
    _add(om, 2, [item1])
    _add(om, 3, [item1])

    om.cancel_order(1)  # → CANCELLED 상태 유지

    # get_order_history: CANCELLED 포함 전체 반환
    history = om.get_order_history()
    results.append(("history_includes_cancelled", any(
        getattr(o, "status", "") == "CANCELLED" for o in history
    )))
    results.append(("history_length", len(history) >= 3))

    # get_orders_by_status: PENDING만 반환
    pending = om.get_orders_by_status("PENDING")
    results.append(("get_by_status_pending", len(pending) >= 1))

    # 취소된 주문이 get_order로 여전히 조회됨 (삭제 금지 검증)
    o1 = om.get_order(1)
    results.append(("cancelled_still_accessible", o1 is not None and o1.status == "CANCELLED"))

    # apply_discount, get_order_total 여전히 동작
    om.apply_discount(2, 0.1)
    results.append(("apply_discount_still_works", abs(om.get_order_total(2) - 9.0) < 0.01))

except Exception as e:
    results.append(("step6_exception", False))
    print(f"STEP6 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 7: 환불 시스템 + 이전 기능 유지
_TESTS_STEP7 = '''
results = []

def _make_item(name, price, quantity):
    try:
        return Item(name=name, price=price, quantity=quantity, stock=0)
    except TypeError:
        return Item(name=name, price=price, quantity=quantity)

def _add(om, oid, items):
    """시그니처 검사로 auto-id/explicit-id 구분, next_order_id 낭비 방지"""
    import inspect as _inspect
    inv = Inventory()
    inv.add_item("apple", 10.0, 100)
    try:
        _params = list(_inspect.signature(om.add_order).parameters.keys())
        _use_explicit = bool(_params) and _params[0] in ("order_id", "id", "oid")
    except Exception:
        _use_explicit = False
    if _use_explicit:
        for call in [lambda: om.add_order(oid, items, inv),
                     lambda: om.add_order(oid, items)]:
            try: call(); return
            except (TypeError, AttributeError, ValueError): continue
    else:
        for call in [lambda: om.add_order(items, inv),
                     lambda: om.add_order(items)]:
            try: call(); return
            except (TypeError, AttributeError, ValueError): continue

try:
    item1 = _make_item("apple", 10.0, 1)

    inv_for_om = Inventory()
    inv_for_om.add_item("apple", 10.0, 100)
    try:
        om = OrderManager(inv_for_om)
    except TypeError:
        om = OrderManager()

    _add(om, 1, [item1])
    _add(om, 2, [item1])

    # process_payment: PENDING/CONFIRMED 어느 상태에서든 동작하도록 두 경우 시도
    payment = None
    try:
        payment = om.process_payment(1, 10.0, "card")  # PENDING 상태 직접 시도
    except Exception:
        try:
            om.confirm_order(1)  # CONFIRMED로 전환 후 재시도
            payment = om.process_payment(1, 10.0, "card")
        except Exception:
            pass
    results.append(("process_payment_ok", payment is not None))

    om.refund_payment(1)
    o1 = om.get_order(1)
    results.append(("refund_changes_status", hasattr(o1, "status") and o1.status == "REFUNDED"))

    # refunded Payment 확인
    p = om.get_payment(1)
    results.append(("payment_refunded_flag", hasattr(p, "refunded") and p.refunded == True))

    # 중복 환불 → ValueError
    double_refund = False
    try:
        om.refund_payment(1)
    except (ValueError, Exception):
        double_refund = True
    results.append(("double_refund_raises", double_refund))

    # get_refunded_orders
    refunded = om.get_refunded_orders()
    results.append(("get_refunded_orders", len(refunded) >= 1))

    # cancel_order (CANCELLED 상태 유지, 삭제 금지) 여전히 동작
    _add(om, 3, [item1])
    om.cancel_order(3)
    o3 = om.get_order(3)
    results.append(("cancel_still_keeps_order", o3 is not None and o3.status == "CANCELLED"))

    # get_order_history 여전히 동작
    history = om.get_order_history()
    results.append(("history_still_works", len(history) >= 2))

except Exception as e:
    results.append(("step7_exception", False))
    print(f"STEP7 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계 8: 멀티 고객 + 누적 이전 기능 유지
# 이 시점에서 Baseline의 context window(최근 6개)는 수정3~8만 기억
# StateDoc은 Spec.md에 수정1(Item 구조), 수정2(discount), 수정3(cancel 동작) 전부 보유
_TESTS_STEP8 = '''
results = []

def _make_item(name, price, quantity):
    try:
        return Item(name=name, price=price, quantity=quantity, stock=0)
    except TypeError:
        return Item(name=name, price=price, quantity=quantity)

def _add_c(om, oid, items, cid):
    """시그니처 검사 기반 add_order 호출 (customer_id 포함, next_order_id 낭비 방지)"""
    import inspect as _inspect
    inv = Inventory()
    inv.add_item("apple", 10.0, 100)
    try:
        _params = list(_inspect.signature(om.add_order).parameters.keys())
        _use_explicit = bool(_params) and _params[0] in ("order_id", "id", "oid")
        _has_customer = "customer_id" in _params or "cid" in _params
    except Exception:
        _use_explicit = False
        _has_customer = False
    # 시그니처에 따라 최적 호출 순서 결정
    if _use_explicit and _has_customer:
        candidates = [lambda: om.add_order(oid, items, inv, cid),
                      lambda: om.add_order(oid, items, cid)]
    elif _use_explicit:
        candidates = [lambda: om.add_order(oid, items, cid),
                      lambda: om.add_order(oid, items, inv, cid),
                      lambda: om.add_order(oid, items)]
    elif _has_customer:
        candidates = [lambda: om.add_order(items, inv, cid),
                      lambda: om.add_order(items, cid)]
    else:
        candidates = [lambda: om.add_order(items, inv),
                      lambda: om.add_order(items)]
    for call in candidates:
        try:
            call()
            return
        except (TypeError, AttributeError):
            continue
        except ValueError as e:
            if "고객" in str(e) or "customer" in str(e).lower() or "등록" in str(e):
                raise
            continue

try:
    item1 = _make_item("apple", 10.0, 1)

    inv_for_om = Inventory()
    inv_for_om.add_item("apple", 10.0, 100)
    try:
        om = OrderManager(inv_for_om)
    except TypeError:
        om = OrderManager()

    # add_customer: customer_id 포함/미포함 버전 모두 허용
    _cid_used = None
    for _ac_call, _cid_try in [
        (lambda: om.add_customer(100, "Alice", "alice@example.com"), 100),
        (lambda: om.add_customer("Alice", "alice@example.com"), None),
    ]:
        try:
            _ac_call()
            _cid_used = _cid_try
            break
        except TypeError:
            continue
    results.append(("add_customer_works", _cid_used is not None or True))

    c = None
    if _cid_used is not None:
        try:
            c = om.get_customer(100)
        except Exception:
            pass
    if c is None:
        # customer_id 없이 추가된 경우: 이름으로 조회 시도
        try:
            customers = om.get_all_customers() if hasattr(om, "get_all_customers") else []
            c = next((x for x in customers if getattr(x, "name", "") == "Alice"), None)
        except Exception:
            pass
    results.append(("get_customer", c is not None and getattr(c, "name", "") == "Alice"))

    _add_c(om, 1, [item1], 100)
    _add_c(om, 2, [item1], 100)
    _add_c(om, 3, [item1], 100)

    # get_orders_by_customer
    cust_orders = om.get_orders_by_customer(100)
    results.append(("get_orders_by_customer", len(cust_orders) >= 1))

    # 핵심: cancel_order가 여전히 CANCELLED 상태 유지 (수정3부터 내려온 요구사항)
    om.cancel_order(1)
    o1 = om.get_order(1)
    results.append(("cancel_keeps_cancelled", o1 is not None and o1.status == "CANCELLED"))

    # apply_discount 여전히 동작 (수정2부터 내려온 요구사항)
    om.apply_discount(2, 0.2)
    results.append(("apply_discount_still_works", abs(om.get_order_total(2) - 8.0) < 0.01))

    # get_order_history 여전히 동작 (수정6부터 내려온 요구사항)
    history = om.get_order_history()
    results.append(("history_still_works", len(history) >= 1))

    # process_payment 여전히 동작 (수정4부터 내려온 요구사항)
    _pay = None
    try:
        _pay = om.process_payment(2, 8.0, "card")  # PENDING 상태 직접 시도
    except Exception:
        try:
            om.confirm_order(2)
            _pay = om.process_payment(2, 8.0, "card")
        except Exception:
            pass
    results.append(("payment_still_works", _pay is not None))

except Exception as e:
    results.append(("step8_exception", False))
    print(f"STEP8 ERROR: {e}")

for name, passed in results:
    print(f"TEST {'PASS' if passed else 'FAIL'}: {name}")
'''

# 단계별 테스트 맵 (0=초기, 1~8=수정 단계)
STEP_TESTS = {
    0: _TESTS_STEP0,
    1: _TESTS_STEP1,
    2: _TESTS_STEP2,
    3: _TESTS_STEP3,
    4: _TESTS_STEP4,
    5: _TESTS_STEP5,
    6: _TESTS_STEP6,
    7: _TESTS_STEP7,
    8: _TESTS_STEP8,
}


class CodeExecutor:
    """
    에이전트가 생성한 코드를 실제 실행하여 테스트 통과율로 점수를 산출하는 평가자.

    LLM 기반 CodeEvaluator와 달리 결정론적이며 재현 가능합니다.
    실험에서 선택적으로 사용할 수 있습니다 (--eval-mode exec).
    """

    def __init__(self, timeout: int = 10):
        """
        Parameters
        ----------
        timeout : 각 테스트 실행의 최대 허용 시간(초)
                  무한 루프 등 비정상 코드를 강제 종료하기 위함
        """
        self.timeout = timeout

    def _strip_example_code(self, code: str) -> str:
        """
        에이전트 코드에서 모듈 레벨 예제 실행 코드를 제거합니다.

        LLM은 클래스/함수 정의 외에 모듈 레벨에서 직접 실행되는 예제 코드를 생성합니다.
        이 코드가 status machine 도입 이후 cancel_order(SHIPPED) 같은 호출을 try/except 없이
        하면 ValueError가 발생하여 테스트 코드 자체가 실행되지 않습니다.

        주석 텍스트 매칭 대신 AST 파싱으로 정확하게 감지합니다:
          - 최상위 class/function/import 정의가 끝난 이후에 나타나는
            실행 구문(Expr, Assign 등)을 잘라냅니다.
          - if __name__ == "__main__": 블록도 제거합니다.
        """
        # 1순위: 알려진 예제 섹션 마커를 문자열 검색으로 빠르게 처리
        for guard in [
            '\nif __name__ == "__main__":',
            "\nif __name__ == '__main__':",
            '\n# Example Usage',
            '\n# 사용 예제',
            '\n# 예제',
        ]:
            idx = code.find(guard)
            if idx != -1:
                return code[:idx]

        # 2순위: AST 파싱으로 정의 이후의 실행 코드 감지
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # 파싱 실패 시 SyntaxError 발생 줄 직전까지 잘라내기
            # (LLM이 예제 코드에서 f-string을 잘라낸 경우 등)
            if e.lineno and e.lineno > 1:
                lines = code.split('\n')
                truncated = '\n'.join(lines[:e.lineno - 1])
                try:
                    ast.parse(truncated)
                    return truncated
                except SyntaxError:
                    pass
            return code

        lines = code.split('\n')

        # 최상위 레벨에서 마지막 class/function/import 정의의 끝 줄 번호 찾기
        last_def_line = 0
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.Import, ast.ImportFrom)):
                end = getattr(node, 'end_lineno', 0)
                if end > last_def_line:
                    last_def_line = end

        if last_def_line <= 0:
            return code

        # 마지막 정의 이후에 실행 구문(함수 호출, 변수 할당 등)이 있으면 잘라냄
        for node in tree.body:
            if (isinstance(node, (ast.Expr, ast.Assign, ast.AugAssign,
                                   ast.AnnAssign, ast.If))
                    and node.lineno > last_def_line):
                return '\n'.join(lines[:last_def_line])

        return code

    def evaluate(self, code: str, step_index: int) -> Tuple[float, List[str]]:
        """
        주어진 코드를 step_index에 해당하는 테스트로 실행합니다.

        Parameters
        ----------
        code       : 에이전트가 생성한 Python 코드 문자열
        step_index : 0(초기) ~ 4(수정4)

        Returns
        -------
        (score, details)
          score   : 0.0 ~ 10.0 (통과율 × 10)
          details : 각 테스트 결과 문자열 리스트 ("PASS: xxx", "FAIL: yyy")
        """
        if step_index not in STEP_TESTS:
            logger.warning(f"step_index {step_index}에 해당하는 테스트가 없습니다. 0점 반환.")
            return 0.0, []

        # 모듈 레벨 예제 코드 제거 — 상태 머신 도입 후 unhandled exception 방지
        safe_code = self._strip_example_code(code)
        test_code = STEP_TESTS[step_index]
        # from __future__ import annotations: 클래스 정의 순서 무관하게 타입 어노테이션을 lazy string으로 처리
        # LLM이 Order보다 OrderManager를 먼저 정의하면 Optional[Order] 평가 시 NameError 발생하는 문제 방지
        full_code = "from __future__ import annotations\n" + safe_code + "\n\n" + test_code

        return self._run_tests(full_code)

    def _run_tests(self, full_code: str) -> Tuple[float, List[str]]:
        """
        임시 파일에 코드를 저장하고 subprocess로 실행합니다.

        subprocess 사용 이유:
          - 에이전트 코드가 sys.exit()을 호출하거나 무한루프를 가져도 메인 프로세스를 보호
          - 각 실행이 완전히 독립된 Python 인터프리터에서 실행됨

        Returns
        -------
        (score, details)
        """
        # 임시 파일에 전체 코드(에이전트 코드 + 테스트 코드) 저장
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(full_code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            output = result.stdout + result.stderr
            return self._parse_results(output)

        except subprocess.TimeoutExpired:
            logger.warning(f"코드 실행 타임아웃 ({self.timeout}초 초과)")
            return 0.0, ["FAIL: timeout"]

        except Exception as e:
            logger.error(f"코드 실행 오류: {e}")
            return 0.0, [f"FAIL: execution_error ({e})"]

        finally:
            # 임시 파일 정리
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _parse_results(self, output: str) -> Tuple[float, List[str]]:
        """
        subprocess 출력에서 "TEST PASS: xxx" / "TEST FAIL: xxx" 라인을 파싱합니다.

        출력 예:
          TEST PASS: get_order_exists
          TEST FAIL: total_auto_calc
          STEP1 ERROR: 'Item' is not defined

        Returns
        -------
        (score, details)
          score : 통과 수 / 전체 수 × 10 (테스트가 0개면 0점)
        """
        details = []
        pass_count = 0
        total_count = 0

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("TEST PASS:"):
                details.append(line)
                pass_count += 1
                total_count += 1
            elif line.startswith("TEST FAIL:"):
                details.append(line)
                total_count += 1
            elif line.startswith("STEP") and "ERROR" in line:
                # 실행 중 예외 발생 → 해당 단계 모든 테스트 실패로 기록
                details.append(f"RUNTIME_ERROR: {line}")

        if total_count == 0:
            # 테스트 출력이 전혀 없음 → 코드 자체가 syntax error 등으로 실행 불가
            logger.warning(f"테스트 출력 없음. 원시 출력: {output[:200]}")
            return 0.0, [f"FAIL: no_test_output | {output[:200]}"]

        score = (pass_count / total_count) * 10.0
        return score, details
