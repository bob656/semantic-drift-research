# 코드 구조 설명 (explore.md)

이 문서는 실험 코드 전체 흐름을 처음 보는 사람도 이해할 수 있도록 설명합니다.

---

## 전체 흐름 한눈에 보기

```
main.py
  │
  ├─ Ollama 서버에 연결 (Client 생성)
  │
  └─ ExperimentRunner 실행
        │
        ├─ [반복 N회]
        │     ├─ BaselineAgent → 코드 작성 → 평가
        │     └─ StateDocAgent → 코드 작성 → 평가
        │
        └─ StatisticalAnalyzer → 통계 분석 → 결과 저장
```

실험은 두 종류의 에이전트(Baseline, StateDoc)에게 **같은 문제**를 주고, 반복 수정을 거치면서 누가 더 품질을 유지하는지 비교합니다.

---

## 1. 두 에이전트의 차이

### BaselineAgent — 대화 기록에만 의존

```
[사용자]: StudentManager 만들어줘
[어시스턴트]: (코드 작성)
[사용자]: 점수 기능 추가해줘
[어시스턴트]: (수정 코드 작성)
...
```

에이전트가 기억하는 것은 **최근 대화 6개** 뿐입니다. 대화가 길어질수록 초반 요구사항이 잊혀집니다.

```python
# baseline_agent.py
def _build_context(self) -> str:
    for entry in self.conversation_history[-6:]:   # 최근 6개만 참조
        ...
```

---

### StateDocAgent — 3개의 문서를 항상 들고 다님

코드를 작성하기 전에 먼저 3개의 문서를 만들고, 매 수정마다 이 문서들을 LLM에게 함께 전달합니다.

| 문서 | 역할 | 변경 여부 |
|---|---|---|
| **Spec.md** | 초기 요구사항 명세 (핵심 기능, 데이터 구조) | 고정 |
| **Constraints.md** | 절대 지켜야 할 규칙 (메서드 이름 변경 금지 등) | 고정 |
| **Plan.md** | 현재까지의 작업 진행 상황 | 수정마다 업데이트 |

```python
# statedoc_agent.py — 수정 요청이 들어올 때마다
def modify_code(self, current_code, modification_request):
    self._update_plan_doc(modification_request)   # Plan.md 먼저 갱신
    return self._modify_with_statedoc(...)        # 문서 3개 + 현재코드 + 수정요청 전달
```

LLM에게 전달되는 프롬프트 구조:
```
## Spec.md    ← "처음부터 이런 시스템이었다"
## Constraints.md  ← "이것만은 절대 바꾸지 마라"
## Plan.md    ← "지금까지 이것들을 했다"
## 현재 코드
## 수정 요청
```

---

## 2. 실험 시나리오 진행 방식

`ExperimentRunner`가 두 에이전트에게 동일한 순서로 문제를 냅니다.

```
초기 과제 → 수정 1 → 수정 2 → 수정 3 → 수정 4
```

각 단계가 끝날 때마다 `CodeEvaluator`가 결과물을 채점합니다. 점수는 총 5개(초기 + 수정 4회) 쌓입니다.

```python
# experiment_runner.py
scores = [initial_score]          # 초기 점수

for modification in modifications:
    current_code = agent.modify_code(current_code, modification)
    score = self.evaluator.evaluate(current_code, modification)
    scores.append(score)          # [초기, 수정1, 수정2, 수정3, 수정4]
```

---

## 3. 평가 방식 (CodeEvaluator)

**평가자도 같은 LLM(qwen2.5-coder)** 입니다. 별도의 사람이나 테스트 코드 없이, LLM이 스스로 채점합니다.

```python
# code_evaluator.py
eval_prompt = f"""
요구사항: {task}          ← 해당 단계의 수정 요청
코드: {code}

평가 기준:
- 요구사항 충족도 (40%)
- 코드 품질 (30%)
- 오류 방지 (30%)

0~10점으로만 답하세요.
"""
```

**중요한 한계:** 평가 기준이 `해당 단계의 수정 요청`만입니다. 수정 3단계를 평가할 때 수정 1, 2에서 만든 기능이 깨졌는지는 확인하지 않습니다.

---

## 4. 드리프트율 계산

```python
# experiment_runner.py
drift = (scores[0] - scores[-1]) / scores[0]
# 예) 초기 8.5점, 최종 8.0점 → (8.5 - 8.0) / 8.5 = 5.9%
```

점수가 올랐을 때(음수)는 0으로 처리합니다. 즉, "얼마나 나빠졌는가"만 측정합니다.

---

## 5. 통계 분석 (StatisticalAnalyzer)

N번 반복 실험에서 얻은 드리프트율들을 모아 통계 검정을 합니다.

```
Baseline  드리프트율: [0.0%, 0.0%, 5.9%]
StateDoc  드리프트율: [0.0%, 0.0%, 0.0%]
```

| 지표 | 의미 |
|---|---|
| **t-검정 p-value** | 두 그룹의 차이가 우연인지 확인. 0.05 미만이면 "유의미한 차이" |
| **Cohen's d** | 효과 크기. 0.2=작음, 0.5=중간, 0.8 이상=매우 큼 |
| **평균 드리프트율** | 반복 실험의 평균 품질 하락률 |

---

## 6. 이번 실험 결과와 한계

### 결과 요약

| | Baseline | StateDoc |
|---|---|---|
| 평균 드리프트율 | 1.96% | 0.0% |
| 실행 시간 (단계당) | 2~10초 | 10~25초 |

StateDoc이 드리프트율 0%로 더 나은 결과를 보였으나, 통계적으로는 유의미하지 않습니다(p=0.374).

### 결과를 신뢰하기 어려운 이유 3가지

**① 실험이 사실상 1번만 한 것과 같음**

`temperature=0.1`이어서 LLM이 매번 거의 같은 코드를 씁니다. StateDoc의 3번 점수가 완전히 동일(`[8.5, 8.5, 9.0, 8.5, 8.5]`)한 것이 증거입니다. 3번 반복했지만 독립적인 샘플이 아닙니다.

**② 평가자가 드리프트를 못 잡음**

단계별로 해당 수정 요청만 평가하므로, 이전 기능이 망가져도 점수에 반영되지 않습니다. 실제로 드리프트가 발생했어도 8~9점 범위 안에서 유지될 수 있습니다.

**③ 시나리오가 너무 쉬움**

StudentManager 수준의 과제는 7B 모델이 쉽게 처리합니다. 두 에이전트 모두 잘 해내서 차이가 드러나지 않습니다.

### 개선하면 달라지는 것

| 변경 | 기대 효과 |
|---|---|
| `temperature 0.1 → 0.5` | 실험 간 독립성 확보 → 통계 검정 의미 생김 |
| 평가를 누적 요구사항 기준으로 변경 | 드리프트 실제 포착 가능 |
| 반복 횟수 10회 이상 | p-value가 유의미해질 가능성 |
| 더 복잡한 시나리오 | 두 에이전트 간 차이 극대화 |

---

## 7. SWT-Bench 적용 가이드

### SWT-Bench란?

SWT-Bench는 실제 GitHub 이슈를 기반으로 한 소프트웨어 엔지니어링 벤치마크입니다. 현재 실험(StudentManager)과의 핵심 차이는 다음과 같습니다.

| 항목 | 현재 실험 | SWT-Bench |
|---|---|---|
| 과제 출처 | 직접 설계한 시나리오 | 실제 GitHub 이슈 |
| 평가 방법 | LLM이 주관적 채점 | 실제 테스트 코드 실행 (pass/fail) |
| 코드베이스 | 새로 작성 | 기존 대규모 저장소 |
| 수정 단계 | 순서대로 4단계 | 이슈 1개당 1개의 패치 |
| 드리프트 정의 | 점수 하락 | 기존 테스트 회귀(regression) 발생 |

---

### 현재 코드에서 바꿔야 할 부분

#### ① `experiment_runner.py` — 시나리오를 SWT-Bench 태스크로 교체

현재는 시나리오가 코드에 하드코딩되어 있습니다.

```python
# 현재 (experiment_runner.py)
self.scenario = {
    'initial_task': 'StudentManager 클래스를 만드세요...',
    'modifications': [ '점수 추가', '등급 추가', ... ]
}
```

SWT-Bench에서는 벤치마크 데이터셋을 읽어서 태스크를 주입해야 합니다.

```python
# SWT-Bench 적용 시 변경 방향
def load_swtbench_task(instance_id: str) -> dict:
    # SWT-Bench 데이터셋에서 이슈 불러오기
    return {
        'repo': 'django/django',
        'issue': '이슈 설명 텍스트',
        'base_commit': 'abc123',       # 수정 전 코드 상태
        'test_patch': '테스트 코드',   # 정답 검증용
    }
```

각 이슈가 1개의 "수정 요청"이 되고, 여러 이슈를 순서대로 적용하면 현재의 4단계 수정과 같은 구조가 됩니다.

---

#### ② `code_evaluator.py` — LLM 채점 → 테스트 실행으로 교체

현재 평가의 가장 큰 문제(주관적 채점, 누적 요구사항 미반영)가 SWT-Bench에서는 자동으로 해결됩니다. 실제 테스트 코드를 실행하면 되기 때문입니다.

```python
# SWT-Bench 적용 시 평가 방식
import subprocess

class SWTBenchEvaluator:
    def evaluate(self, patched_code: str, test_patch: str) -> float:
        # 1. 패치를 저장소에 적용
        # 2. pytest 실행
        result = subprocess.run(['pytest', '--tb=no', '-q'], capture_output=True)

        # 3. 통과한 테스트 비율을 점수로 환산
        passed = parse_test_results(result.stdout)
        return passed / total_tests * 10.0
```

이렇게 하면 평가가 객관적이 되고, 기존 테스트가 깨지면(드리프트) 점수가 실제로 하락합니다.

---

#### ③ `agents/` — 에이전트에게 저장소 컨텍스트 제공

현재 에이전트는 빈 파일에서 코드를 새로 작성하지만, SWT-Bench에서는 **기존 대규모 코드베이스를 이해하고 패치**해야 합니다.

```python
# BaselineAgent — 관련 파일 내용을 대화 히스토리에 추가
def solve_initial(self, task: str, repo_context: str) -> str:
    prompt = f"""
관련 파일:
{repo_context}        ← 수정 대상 파일들

이슈:
{task}

위 코드에서 이슈를 해결하는 패치를 작성하세요.
"""

# StateDocAgent — Spec.md에 저장소 구조 반영
def _initialize_state_docs(self, task: str, repo_context: str):
    # Spec.md: 이슈 요구사항 + 저장소의 기존 API 구조
    # Constraints.md: 기존 테스트를 깨면 안 된다는 규칙 추가
    # Plan.md: 어떤 파일을 수정할지 계획
```

---

### SWT-Bench 적용 단계별 순서

```
1단계: 환경 구성
  - SWT-Bench 데이터셋 다운로드
  - Docker 또는 가상환경으로 각 저장소 실행 환경 구성
  - pytest 실행 가능한지 확인

2단계: 데이터 로더 작성
  - runner/swtbench_loader.py 추가
  - 인스턴스 ID로 이슈/저장소/테스트 불러오는 함수 구현

3단계: 평가자 교체
  - evaluator/code_evaluator.py → evaluator/test_runner_evaluator.py
  - LLM 채점 대신 pytest 결과를 점수로 변환

4단계: 에이전트 수정
  - solve_initial()에 repo_context 파라미터 추가
  - StateDocAgent의 Constraints.md에 "기존 테스트 보존" 규칙 강화

5단계: 드리프트 재정의
  - 현재: (초기점수 - 최종점수) / 초기점수
  - SWT-Bench: (초기 통과 테스트 수 - 최종 통과 테스트 수) / 초기 통과 테스트 수
  - 또는: 새 이슈를 해결하면서 기존 테스트가 몇 개나 깨지는지 (regression rate)
```

---

### SWT-Bench에서 드리프트의 의미

현재 실험에서 드리프트는 "LLM이 주관적으로 점수를 낮게 줬다"는 뜻입니다. SWT-Bench에서는 드리프트가 훨씬 명확해집니다.

```
이슈 1 해결 후: 기존 테스트 100개 중 100개 통과  → 드리프트 없음
이슈 2 해결 후: 기존 테스트 100개 중 95개 통과   → 드리프트 5%
이슈 3 해결 후: 기존 테스트 100개 중 88개 통과   → 드리프트 12%
```

StateDocAgent가 Constraints.md에 "기존 테스트 보존" 규칙을 명시해두면, 이 regression을 줄이는 효과를 측정할 수 있습니다. 이것이 이 연구의 핵심 가설을 실제 벤치마크에서 검증하는 방법입니다.
