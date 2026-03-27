# 실험 의사결정 기록 (decisions.md)

각 변경의 **원인 → 조치 → 결과**를 순서대로 기록합니다.
새로운 문제가 발견되거나 코드를 수정할 때마다 여기에 추가합니다.

---

## 결정 1 — `__init__.py` 생성 및 파일 구조 완성

**날짜:** 2026-03-25

### 원인
`agents/init.py`가 `__init__.py`로 잘못 명명되어 있었고,
`evaluator/`, `runner/`, `analyzer/` 폴더에 `__init__.py`가 없었습니다.
Python은 `__init__.py`가 없으면 해당 폴더를 패키지로 인식하지 못합니다.

```
from runner import ExperimentRunner  ← 이 import가 실패함
```

### 조치
- `agents/__init__.py` 생성
- `evaluator/__init__.py`, `runner/__init__.py`, `analyzer/__init__.py` 생성

### 결과
모듈 import가 정상 작동합니다.

---

## 결정 2 — 원격 Ollama 연결 지원

**날짜:** 2026-03-25

### 원인
Ollama 서버가 다른 컴퓨터에 설치되어 있어 `ollama.chat()`을 로컬에서 직접 호출할 수 없었습니다.

### 조치
- `ollama.Client(host=...)` 방식으로 변경
- `main.py`에 `--host` CLI 인자 추가 (기본값: `http://localhost:11434`)
- 클라이언트 객체를 모든 에이전트와 평가자에게 전달

### 결과
```bash
python main.py --host http://192.168.100.52:11434
```
명령으로 원격 Ollama 서버에 연결할 수 있습니다.

---

## 결정 3 — NaN 버그 수정

**날짜:** 2026-03-25
**파일:** `analyzer/statistical_analyzer.py`

### 원인
gemma3:12b 실험(174711)에서 두 그룹의 드리프트율이 모두 `[0.0, 0.0, 0.0]`이었습니다.
표준편차가 0이 되면서 `scipy.ttest_ind`가 NaN을 반환했고,
JSON 결과에 `"t_statistic": NaN`이 저장되어 분석이 불가능했습니다.

```
두 그룹 분산 = 0  →  pooled_std = 0  →  0/0 = NaN
```

### 조치
t-검정 결과에 `math.isnan()` 체크를 추가하여 NaN 발생 시 `(t=0.0, p=1.0, d=0.0)`으로 폴백 처리

```python
if math.isnan(t_stat) or math.isnan(p_value):
    t_stat, p_value, cohens_d = 0.0, 1.0, 0.0
```

### 결과
104926 실험부터 `"t_statistic": 0.0, "p_value": 1.0`으로 정상 저장됩니다.

---

## 결정 4 — 평가 기준을 누적 요구사항으로 변경

**날짜:** 2026-03-25
**파일:** `runner/experiment_runner.py`

### 원인
기존 평가는 해당 단계의 수정 요청만을 기준으로 점수를 매겼습니다.

```
수정3 평가 시:
  기준 → "save_to_file 메서드를 추가하세요"  (수정3 요청만)
  판단 → save_to_file 잘 구현됨 → 9점

실제로는 수정1에서 만든 add_score가 사라졌어도
평가자는 수정3 요청만 보므로 이를 감지하지 못함
```

이것이 드리프트율이 항상 0%였던 근본 원인입니다.

### 조치
평가 시 초기 과제부터 현재 단계까지의 모든 요구사항을 합산하여 전달

```python
# 수정3 평가 시 전달되는 기준:
[요구사항 0] StudentManager 기본 구조 (add/get/remove_student)
[요구사항 1] add_score, get_scores 추가
[요구사항 2] get_average, get_grade 추가
[요구사항 3] save_to_file, load_from_file 추가
```

### 결과
122254 실험에서 처음으로 드리프트가 측정되었습니다.
StateDoc Run 2: 초기 9.5 → 수정1에서 9.0으로 하락 → **드리프트 포착**

### 부작용 (→ 결정 6으로 이어짐)
StateDoc이 초기에 9.5점을 받았다가 수정1에서 9.0이 되자
비율 공식 `(9.5-9.0)/9.5 = 5.26%`로 드리프트가 계산되었습니다.
Baseline은 처음부터 9.0으로 시작해서 드리프트 0%.
**절대 점수 수준은 같은데 드리프트율은 StateDoc이 더 높게 나오는 왜곡 발생.**

---

## 결정 5 — 드리프트 공식을 최솟값 기반으로 변경

**날짜:** 2026-03-25
**파일:** `runner/experiment_runner.py`

### 원인
기존 공식 `(초기 - 최종) / 초기`는 중간에 점수가 하락했다가 회복되면 드리프트를 0%로 처리했습니다.

```
예) 점수 흐름: [9.0, 9.0, 9.0, 8.5, 9.2]
    최종(9.2) > 초기(9.0) → 드리프트 0%
    그러나 수정3에서 8.5로 떨어진 실제 하락은 측정되지 않음
```

### 조치
최종값 대신 전체 구간의 최솟값으로 비교

```python
drift = (scores[0] - min(scores)) / scores[0]
```

### 결과
`[9.0, 9.0, 9.0, 8.5, 9.2]`의 드리프트가 `(9.0-8.5)/9.0 = 5.6%`로 포착됩니다.
중간에 발생한 하락이 측정됩니다.

---

## 결정 6 — 드리프트 공식을 절대 하락량으로 변경

**날짜:** 2026-03-25
**파일:** `runner/experiment_runner.py`, `main.py`

### 원인
결정 4의 부작용으로, 비율 공식이 초기 점수에 따라 결과가 달라졌습니다.

```
같은 0.5점 하락인데:
  초기 9.5 → 9.0: 0.5 / 9.5 = 5.26%  (StateDoc, 불리)
  초기 9.0 → 8.5: 0.5 / 9.0 = 5.56%  (Baseline)
```

StateDoc이 초기에 더 좋은 코드를 만들수록 오히려 드리프트율이 낮게 나오는 역설이 발생했습니다.

### 조치
분모(초기 점수)를 제거하고 절대 하락량만 측정

```python
drift = scores[0] - min(scores)  # 단위: 점수 (0~10 척도)
```

출력 포맷도 `:.1%` → `:.3f점` 으로 변경

### 결과
```
같은 0.5점 하락 → 두 에이전트 모두 0.500점으로 동일하게 측정
```
초기 점수가 높든 낮든 공정하게 비교할 수 있습니다.

---

---

## 결정 7 — 충돌 유발형 시나리오로 교체 (OrderSystem)

**날짜:** 2026-03-25
**파일:** `runner/experiment_runner.py`

### 원인
StudentManager 시나리오는 모든 수정이 순수 추가(additive)로 이루어져 드리프트가 발생하기 어려웠습니다.
기존 기능을 수정하거나 동작을 변경하는 요청이 없으면, 에이전트가 이전 코드를 유지하는 것이 자연스럽습니다.

### 조치
OrderSystem Evolution 시나리오로 교체:
- **수정1**: Item dataclass 도입 → `add_order` 시그니처 변경, `total` 자동계산으로 전환
- **수정2**: 할인 시스템 → `total` 계산 로직 변경 (이전 자동계산 방식과 충돌)
- **수정3**: 상태 머신 → `cancel_order` 동작 변경 (단순 삭제 → 상태 전환, SHIPPED 시 예외)
- **수정4**: 결제 통합 → `process_payment`와 `confirm_order` 역할 충돌

### 예상 효과
StateDoc은 Spec.md/Plan.md/Constraints.md에 변경 이력을 기록하므로
수정3에서 `cancel_order`가 어떻게 바뀌었는지 추적할 수 있습니다.
Baseline은 sliding window(최근 6개 메시지)에 이전 동작이 남아있지 않으면
기존 메서드를 잘못 변경하거나 누락할 가능성이 높습니다.

---

## 결정 8 — temperature 0.1 → 0.5 상향

**날짜:** 2026-03-25
**파일:** `agents/base_agent.py`

### 원인
temperature=0.1은 거의 결정론적 출력을 생성하여 동일 반복 실험에서 항상 같은 코드가 나왔습니다.
이로 인해 3회 반복이 실질적으로 독립적이지 않았습니다.

### 조치
```python
temperature: float = 0.1  →  temperature: float = 0.5
```

### 결과
실험 간 다양성이 증가하여 통계적으로 의미 있는 분산이 나타날 것으로 기대됩니다.

---

## 결정 9 — 코드 실행 기반 평가 추가 (eval_mode='exec')

**날짜:** 2026-03-25
**파일:** `evaluator/code_executor.py` (신규), `runner/experiment_runner.py`, `main.py`

### 원인
LLM 평가(CodeEvaluator)는 주관적이고 재현 불가합니다.
같은 코드도 평가 시점에 따라 점수가 달라질 수 있어 드리프트 측정이 불안정합니다.

### 조치
- `CodeExecutor` 클래스 신규 생성: OrderSystem 시나리오 각 단계별 Python 테스트 케이스 정의
- subprocess로 에이전트 코드를 격리 실행 → 통과 테스트 수 / 전체 × 10 = 점수
- `main.py`에 `--eval-mode llm|exec` 옵션 추가
- `ExperimentRunner`에 `eval_mode` 파라미터 추가 → `_score()` 메서드로 분기

### 테스트 케이스 (누적 — 이전 단계 기능 포함)
| 단계 | 테스트 수 | 핵심 검증 항목 |
|---|---|---|
| 0 (초기) | 4개 | add/get/cancel/list_order |
| 1 (수정1) | 7개 | Item 클래스, total 자동계산, 이전 기능 유지 |
| 2 (수정2) | 6개 | apply_discount, get_order_total, 이전 기능 유지 |
| 3 (수정3) | 7개 | 상태 전환, cancel SHIPPED 예외, 이전 기능 유지 |
| 4 (수정4) | 8개 | process_payment, 금액 불일치 예외, 이전 기능 유지 |

### 사용 방법
```bash
python main.py --eval-mode exec --host http://192.168.100.52:11434
```

---

## 결정 10 — apply_discount 테스트 단위 버그 수정

**날짜:** 2026-03-26
**파일:** `evaluator/code_executor.py`, `runner/experiment_runner.py`

### 원인
`debug_baseline/step2_mod2.py` 확인 결과, LLM은 `apply_discount`를 두 가지 방식으로 잘못 구현했습니다.

1. **위치 오류**: `apply_discount`를 `OrderManager`가 아닌 `Order` 인스턴스 메서드로 구현
   - 테스트 `om.apply_discount(1, 0.1)` → `AttributeError`
2. **단위 불일치**: 시나리오 프롬프트가 할인율 범위를 명시하지 않아 LLM이 0.0~1.0 방식을 선택했으나 테스트는 10.0(=10%)을 전달

### 조치
- 시나리오 프롬프트에 `OrderManager에 apply_discount 추가` 명시 + `0.0~1.0 범위 (0.1=10%)` 명시
- 테스트 코드: `10.0` → `0.1`, `20.0` → `0.2` (step2, step3, step4 전체 수정)

---

## 결정 11 — extract_code 닫는 fence 미처리 버그 수정

**날짜:** 2026-03-26
**파일:** `agents/base_agent.py`

### 원인
LLM(gemma3:12b)이 응답 마지막에 닫는 ` ``` `를 생략하는 경우가 있었습니다.
기존 코드는 `end == -1`이면 조용히 건너뛰어 전체 응답(` ```python ... ` 포함)을 반환했습니다.

```
오염된 코드 → 다음 단계 프롬프트에 포함 → 중첩 fence 생성 → 연쇄 SyntaxError
```

`debug_statedoc/step4_mod4.py` 파일 첫 줄이 ` ```python `이었습니다.
이것이 StateDoc이 항상 drift=10.0을 기록한 원인이었습니다.

### 조치
```python
# 1. 닫는 ``` 없어도 opening 이후 내용 전체 반환
if end != -1:
    code = text[start:end].strip()
else:
    code = text[start:].strip()   # ← 추가

# 2. 안전장치: 결과가 여전히 ``` 로 시작하면 강제 제거
if code.startswith("```"):
    first_newline = code.find("\n")
    code = code[first_newline + 1:].strip()
```

---

## 결정 12 — StateDocAgent temperature 0.1 → 0.5

**날짜:** 2026-03-26
**파일:** `agents/statedoc_agent.py`

### 원인
`base_agent.py`의 기본값을 0.5로 올렸지만, `StateDocAgent.__init__`가 `temperature: float = 0.1`을 명시적으로 덮어써서 반영되지 않았습니다.
결과적으로 StateDoc의 3회 반복이 여전히 동일한 결과를 냈습니다.

### 조치
```python
temperature: float = 0.1  →  temperature: float = 0.5
```

---

## 결정 13 — 테스트 인프라 전면 수정 (steps 5-8)

**날짜:** 2026-03-27

### 원인
steps 6-8이 항상 0.0점인 핵심 원인 3가지:

1. **`OrderManager()` 생성자 버그**: mod5 이후 에이전트가 `OrderManager(inventory)` 필수 파라미터를 생성함. 테스트는 `om = OrderManager()`로 시작 → TypeError → score=0.0

2. **`next_order_id` 낭비 문제**: `_add` 헬퍼가 wrong-type 호출 시 함수 내부에서 TypeError 발생 → `next_order_id`는 이미 증가 → fallback 호출이 order_id=2로 생성 → `get_order(1)` → None → 이후 모든 테스트 실패

3. **SyntaxError 미처리**: LLM이 예제 코드의 f-string을 잘라낸 경우, `ast.parse` 실패 시 원본 코드 반환 → subprocess SyntaxError → score=0.0

### 조치
- **`_strip_example_code`**: `# Example Usage`, `# 사용 예제` 주석도 1순위로 탐색. SyntaxError 발생 시 `e.lineno`로 해당 줄 직전까지 잘라내기
- **모든 `_add` 헬퍼**: `inspect.signature`로 첫 번째 파라미터 이름 확인 → `order_id` → explicit-id 호출, `items` → auto-id 호출. 불필요한 실패 시도 제거
- **`OrderManager` 생성자**: `try: om = OrderManager(Inventory())` + `except TypeError: om = OrderManager()` 패턴
- **`_make_item` 헬퍼**: `stock=0` 파라미터 포함/미포함 모두 허용
- **steps 3, 4 `_add`도 동일 수정**

### 결과
디버그 파일 기준:
- Baseline: steps 0-8 모두 10.0 → drift=0.0
- StateDoc: step6에서 `add_order`가 items를 tuple로 unpacking → TypeError → order 생성 실패 → drift=10.0

이는 StateDoc이 Baseline보다 더 많이 drift되는 실제 결과. StateDoc이 spec에서 코드를 재생성할 때 Item 객체 대신 tuple 형식으로 퇴행하는 것이 원인.

---

## 아직 해결되지 않은 문제

| 문제 | 설명 | 해결 방향 |
|---|---|---|
| 샘플 부족 | 3회 반복으로는 통계적 유의성 검증 불가 | `--repeats 10` 이상 권장 |
| 가설 방향 역전 가능성 | Baseline이 기존 코드를 그대로 전달하므로 구현 세부사항이 보존됨. StateDoc은 spec에서 재생성하므로 tuple 퇴행 등이 발생 | 다수 반복 실험으로 패턴 확인 필요 |

---

## 실험 이력 요약

| 실험 | 모델 | 주요 변경 | Baseline | StateDoc | 개선 |
|---|---|---|---|---|---|
| 163921 | qwen2.5-coder:7b | 최초 실험 | 1.96% | 0.0% | +1.96% |
| 174711 | gemma3:12b | 모델 변경 | 0.0% | 0.0% | NaN |
| 104926 | gemma3:12b | NaN 버그 수정 | 0.0% | 0.0% | 0.0% |
| 122254 | gemma3:12b | 누적 평가 + 최솟값 공식 | 0.0% | 1.75% | -1.75% (왜곡) |
| 142427 | gemma3:12b | 절대 하락량 공식 | 0.167점 | 0.167점 | 0.000점 |
| 161738 | gemma3:12b | 충돌 시나리오 + exec 평가 + temp=0.5 | 10.0점 | 10.0점 | 0.000점 (테스트 버그) |
| 174419 | gemma3:12b | apply_discount 래퍼 수정 | 3.75점(±5.45) | 10.0점(±0) | -6.25점 (StateDoc fence 오염 버그) |
| 100617~170507 | gemma3:12b | 8단계 확장, exec 평가 | 균등 실패 | 균등 실패 | 0점 (테스트 버그) |
| 다음 실험 | gemma3:12b | 테스트 인프라 전면 수정 | ? | ? | ? |
