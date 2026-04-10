# codexCv

`codexCv`는 반복적 코드 수정 과정에서 발생하는 semantic drift를 측정하기 위한 벤치마크 스캐폴드다.

핵심 목표는 두 단계다.

1. `Controlled DriftBench`
직접 설계한 수정 시퀀스로 논문의 핵심 주장을 세운다.

2. `Benchmark-Derived EditSet`
기존 `HumanEval+`와 `MBPP+` 문제에서 파생한 수정 시퀀스로 외적 타당성을 보강한다.

## 디렉터리 구조

```text
codexCv/
├── README.md
├── schemas/
│   └── scenario.schema.json
├── runner/
│   ├── __init__.py
│   ├── catalog.py
│   ├── inspect.py
│   └── load_scenario.py
└── scenarios/
    ├── controlled/
    │   ├── order_system_v1/
    │   └── budget_tracker_v1/
    └── derived/
        ├── humaneval_plus/
        │   └── he_string_span_edit/
        └── mbpp_plus/
            └── mbpp_discount_cap_edit/
```

## 설계 원칙

- 평가 단위는 `single-shot task`가 아니라 `edit sequence`다.
- 각 step는 `새 요구사항 성공`과 `기존 계약 보존`을 분리 평가한다.
- 계약은 사후 해석이 아니라 `scenario.json`에 사전 정의한다.
- 계약은 가능한 한 `exec`, `ast`, `regex` 같은 기계적 체크로 환원한다.
- `controlled`와 `derived`를 분리해 내적 타당성과 외적 타당성을 따로 확보한다.

## 상태 문서 포맷

상태 문서는 사람이 바로 읽을 수 있도록 `thin blueprint + delta` 구조를 강제한다.

```json
{
  "schema_version": "codexCv-state-v1",
  "step_id": 2,
  "loop_id": 1,
  "blueprint": {
    "entities": [],
    "public_api": [],
    "state_transitions": [],
    "invariants": []
  },
  "delta": {
    "changed": [],
    "unchanged": [],
    "removed": []
  },
  "risks": [],
  "grounding_notes": []
}
```

의미:

- `blueprint`: 계속 유지되어야 하는 얇은 핵심 구조
- `delta.changed`: 이번 step에서 실제로 바뀐 사실
- `delta.unchanged`: 이번 step에서도 유지된 중요한 사실
- `delta.removed`: 더 이상 참이 아닌 이전 사실
- `risks`: 현재 코드 기준의 위험 신호
- `grounding_notes`: 어떤 코드 사실을 근거로 적었는지

## 시나리오 포맷

각 시나리오는 아래 요소를 가진다.

- `step0`: 초기 구현 프롬프트와 초기 기능 테스트
- `steps`: 후속 수정 요청 목록
- `contracts`: 수정과 무관하게 유지되어야 하는 invariant 목록
- `evaluation`: task test와 contract test를 어떤 방식으로 실행할지에 대한 메타데이터

## 포함된 샘플

### Controlled DriftBench

- `order_system_v1`
  - 상태 전이, API 안정성, 총액 일관성을 추적
- `budget_tracker_v1`
  - 예산 상한, 잔액 보존, 정산 semantics를 추적

### Benchmark-Derived EditSet

- `he_string_span_edit`
  - HumanEval+ 스타일 함수에서 시그니처와 경계조건 보존을 추적
- `mbpp_discount_cap_edit`
  - MBPP+ 스타일 함수에서 상한값과 할인 semantics를 추적

## 빠른 확인

시나리오 메타데이터를 확인하려면:

```bash
python -m codexCv.runner.inspect --list
python -m codexCv.runner.inspect --scenario controlled/order_system_v1
```

Baseline harness를 실행하려면:

```bash
python -m codexCv.runner.baseline_runner \
  --scenario controlled/order_system_v1 \
  --host http://192.168.100.52:11434 \
  --model qwen2.5-coder:7b
```

이 baseline은 다음 루프를 수행한다.

1. `Generator`가 코드와 상태 문서를 함께 생성
2. 자동 검사기가 syntax와 probe를 기록
3. `Evaluator`가 구조화된 JSON critique를 반환
4. 기준 미달이면 `Refiner` 프롬프트로 재수정

현재 포함된 `NullCheckProvider`는 syntax와 일부 AST probe만 실행한다. 실험용으로 쓰려면 task tests와 contract tests를 실제 executor에 연결해야 한다.

실행 결과는 두 형태로 저장된다.

- 요약 결과 JSON: `codexCv/results/<scenario>_<timestamp>.json`
- 눈으로 확인하는 loop별 산출물: `codexCv/results/<scenario>_<timestamp>/stepX_loopY/`

loop별 폴더에는 다음 파일이 들어간다.

- `request.md`
- `state_document.json`
- `state_document.md`
- `candidate.py`
- `automated_checks.json`
- `evaluator.json`

## 다음 구현 포인트

- 실제 에이전트 실행기와 연결
- task/contract test 자동 실행기 추가
- HumanEval+/MBPP+ 원본 문제에서 derived 시나리오를 생성하는 importer 추가
- inter-annotator review 기록 필드 추가
