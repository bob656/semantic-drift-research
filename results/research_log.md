# LLM 코딩 에이전트 의미 드리프트 연구 — 연구 일지

> 최종 업데이트: 2026-04-07

---

## 연구 목적

LLM 코딩 에이전트가 반복 수정 과정에서 이전 기능을 잃어가는 현상(**Semantic Drift**)을 측정하고,
다양한 메모리/요약 전략이 이를 줄이는지 검증한다.

**핵심 가설:** 컨텍스트를 구조적으로 관리하는 에이전트는 단순 대화 이력 기반 베이스라인보다 드리프트가 적다.

---

## 에이전트 진화 이력

| 버전 | 파일 | 전략 | 결과 요약 |
|---|---|---|---|
| BaselineAgent | `agents/baseline_agent.py` | 최근 6개 메시지, 코드 300자 절단 | 비교 기준 (Control) |
| StateDocAgent | `agents/statedoc_agent.py` | Spec+Plan+Constraints 3문서 유지 | 가설 반증 — Baseline보다 나쁨 |
| CoTDocAgent (LLM 요약) | `agents/cot_agent.py` (구버전) | LLM이 CoT 분석 생성, 맨 앞 배치 | Baseline 미달 (hallucination) |
| CoTDocAgent (AST) | `agents/cot_agent.py` (현재) | AST 추출 + Recursive Summary | Baseline 미달 (의미적 계약 미흡) |
| LayeredMemoryAgent | `agents/layered_memory_agent.py` | Layer1(영구인터페이스) + Layer2(Delta이력) + Layer3(현재코드) | 현재 실험 중 |
| SemanticCompressorAgent | `agents/semantic_compressor_agent.py` | AST 타입 계약 + 상태 전이 규칙 + 중요도 가중 Delta | 현재 실험 중 |

---

## 실험 이력

### Phase 1: LLM 채점 모드 (2026-03-24~25)

| 실험 파일 | 모델 | Baseline 드리프트 | 비교군 드리프트 | 비고 |
|---|---|---|---|---|
| 163921 | qwen2.5-coder:7b | 1.96% | 0.0% (StateDoc) | 드리프트 역방향 |
| 174711 | gemma3:12b | 0.0% | 0.0% | NaN 버그 발견 |
| 104926 | gemma3:12b | 0.0% | 0.0% | 천장 효과 |
| 122254 | gemma3:12b | 0.0% | 1.75% | 비율 공식 왜곡 |
| 142427 | gemma3:12b | 0.167점 | 0.167점 | 차별화 안 됨 |

**결론:** LLM 채점이 코드 변화를 감지 못함 → exec 모드 전환 결정

---

### Phase 2: exec 모드 도입 + 테스트 인프라 수정 (2026-03-25~27)

| 실험 파일 | Baseline | StateDoc | 비고 |
|---|---|---|---|
| 161738, 174419 | 10.0점 | 10.0점 | 테스트 버그 — step6~8 항상 0.0 |
| 165031, 175831 | 3.75~5.0점 | 10.0점 | 수정 중 |
| 100617 | 3.33점 | 7.14점 | 수정 중 |
| 123933 | 0.0점 | 10.0점 | 수정 중 |

**수정한 테스트 버그 5개:**
1. OrderManager() 생성자 파라미터 불일치 → `try/except` 처리
2. `next_order_id` 낭비 → `inspect.signature`로 파라미터 판별
3. SyntaxError 처리 미흡 → `e.lineno`로 코드 절단
4. `_strip_example_code` 마커 부족 → "# 사용 예제" 등 추가
5. Item `stock` 필드 → `_make_item` 헬퍼로 선택적 처리

---

### Phase 3: StateDoc 정식 실험 (2026-03-30)

**pilot_20260330_133033.json** — 5회 반복 (qwen2.5-coder:14b → 당시 model 확인 필요)

| | Baseline | StateDoc |
|---|---|---|
| 평균 드리프트 | 4.57 ± 4.99 | 10.00 ± 0.00 |
| p-value | 0.041 | |
| Cohen's d | -1.54 (매우 큰 효과, **역방향**) | |

**실패 원인:**
- StateDoc이 추상 문서에서 타입 재해석: `List[Item]` → `(name, quantity)` 튜플
- `Order.calculate_total()`에서 `item.price` 접근 → `AttributeError`
- StateDoc은 5번 모두 drift=10.0 (최악)

---

### Phase 4: CoTDoc-LLM (2026-03-31)

**pilot_20260331_135436.json, 170911.json** — 각 5회

| | Baseline | CoTDoc-LLM |
|---|---|---|
| 범위 | 6.00~8.29 | 8.00~10.00 |
| p-value | > 0.34 | |

**실패 원인:** Lost in the Middle (Liu et al., TACL 2024)
- CoT 분석이 Spec/Plan과 현재 코드 사이 "중간"에 배치 → LLM이 무시
- LLM 생성 요약 자체의 hallucination

---

### Phase 5: CoTDoc-AST (2026-03-31)

**pilot_20260331_205441.json** — 5회

| | Baseline | CoTDoc-AST |
|---|---|---|
| 평균 드리프트 | 8.00 ± 2.98 | 10.00 ± 0.00 |
| p-value | 0.172 | |

**적용 연구:**
- Lost in the Middle (2024): Summary를 프롬프트 맨 앞 배치
- LLMLingua (EMNLP 2023): LLM 요약 → AST 추출 (hallucination 제거)
- Recursive Summarization (2025): `cumulative_summary` 누적
- Chain of Density (2023): 구체적 엔티티 중심 요약

**실패 원인:**
- step5: inventory 스코프 오류 (AST 시그니처로는 의미적 계약 불가)
- step6,8: SyntaxError — gemma3:12b 코드 생성 불안정
- step7: `get_payment` 소실 — 깨진 코드를 기준으로 AST 추출하는 오류 누적

---

### Phase 6: LayeredMemory + SemanticCompressor 도입 (2026-04-01~07)

**설계 변경:**
- 모델 변경: `gemma3:12b` → `qwen2.5-coder:14b` (코드 생성 안정성)
- 시나리오 축소: 9단계 → 7단계 (step7 환불, step8 멀티고객 제거 — 드리프트는 step6에서 이미 포착)
- timeout: `600초` (qwen2.5-coder:14b 응답 시간 대응)
- `max_tokens`: `2048 → 4096` (SyntaxError — 코드 생성 잘림 문제 해결)

**Harness Engineering 도입 (DRIFT_PROBE 테스트):**
step4, step5, step6에 이전 단계 계약 검증 테스트 추가

| 단계 | DRIFT_PROBE |
|---|---|
| step4 | step1 Item.price 계산, step3 cancel→CANCELLED 보존 |
| step5 | step1 price×qty, step2 discount 10% 계산 |
| step6 | step1 price/qty 속성, step2 discount 비율, step3 cancel 보존 + 이력 |

---

### Phase 7: 최신 실험 결과 (pilot_20260407_005541.json)

**설정:** qwen2.5-coder:14b, 5회 반복, exec 모드, 7단계 시나리오

| | Baseline | LayeredMemory | SemanticCompressor |
|---|---|---|---|
| 평균 드리프트 | **10.0 ± 0.0** | 6.62 ± 4.64 | 6.62 ± 4.64 |
| p-value (vs Baseline) | — | 0.142 | 0.142 |
| Cohen's d | — | 1.03 (매우 큰 효과) | 1.03 |

**단계별 점수 (모든 run 동일):**

| 단계 | Baseline |
|---|---|
| step0 | 10.0 |
| step1 | 10.0 |
| step2 | 8.57 |
| step3 | 8.57 |
| step4 | 9.0 |
| step5 | 7.78 |
| step6 | **0.0** |

**문제점:**
1. **Baseline 5회 완전 동일** — temperature=0.1 버그 (→ 0.5로 수정 완료, 재실험 필요)
2. **LayeredMemory == SemanticCompressor** — run0,1은 drift=2.0/1.11, run2~4는 drift=10.0 (step6에서 완전 붕괴)
3. **p=0.142 비유의** — n=5 부족, 또는 Baseline이 결정론적이어서 분산=0
4. step6 0.0: `get_order_history` + `created_at` 구현 시 코드 전체 붕괴 패턴

---

## 인프라 버그 이력

| 날짜 | 버그 | 원인 | 수정 |
|---|---|---|---|
| 2026-03-25 | step6~8 항상 0.0 | 테스트 코드 5가지 버그 | 각각 수정 |
| 2026-03-25 | LLM 채점 변화 미감지 | 채점 기준 모호 | exec 모드 전환 |
| 2026-03-31 | SyntaxError 다수 | max_tokens=2048 코드 잘림 | 4096으로 증가 |
| 2026-03-31 | IndentationError | compress_code가 빈 if블록 생성 | compression 롤백 |
| 2026-04-01 | Ollama timeout (~146s) | httpx 기본 timeout | Client(timeout=600) |
| 2026-04-07 | Baseline 5회 동일 | temperature=0.1 결정론적 | 0.5로 수정 |
| 2026-04-07 | DRIFT_PROBE JSON 미저장 | _score()가 details 버림 | (score, details) 튜플 반환으로 수정 |

---

## 핵심 설계 결정

| 번호 | 결정 | 이유 |
|---|---|---|
| 1 | exec 모드 | LLM 채점이 코드 변화 감지 못함 |
| 2 | 7단계 시나리오 | 드리프트는 step6에서 발생, 이후 단계 불필요 |
| 3 | temperature=0.5 | 실험 간 독립성 확보 (0.1은 결정론적) |
| 4 | drift = scores[0] - min(scores) | 절대 하락량, 초기점수 의존성 제거 |
| 5 | AST 추출 | LLM 요약의 hallucination 제거 |
| 6 | 중요 정보를 프롬프트 앞/끝 배치 | Lost in the Middle (Liu et al., 2024) |
| 7 | Delta 이력 방식 | 전체 코드보다 변경점만 기록이 의미적으로 정확 |
| 8 | step0 가이드라인 불변 | 오류 누적 방지 |
| 9 | DRIFT_PROBE 테스트 | 어느 단계에서 어떤 계약이 깨지는지 기계적 측정 |
| 10 | max_tokens=4096 | 코드 생성 중단으로 인한 SyntaxError 방지 |

---

## 참고 논문

| 논문 | 어디에 반영 |
|---|---|
| Lost in the Middle (Liu et al., TACL 2024, arxiv:2307.03172) | 중요 정보 프롬프트 앞/끝 배치 |
| LLMLingua (Jiang et al., EMNLP 2023, arxiv:2310.06839) | LLM 요약 → AST 추출 |
| MemGPT (Packer et al., arxiv:2310.08560) | 계층적 메모리 구조 |
| Recursive Summarization (arxiv:2308.15022) | Delta 누적 요약 |
| Chain of Density (Adams et al., 2023) | 구체적 엔티티 중심 요약 |
| SWE-bench-CL (arxiv:2507.00014) | Continual learning for coding agents |

---

## 현재 상태 (2026-04-07)

**완료:**
- [x] temperature 0.5로 수정 (`agents/baseline_agent.py`)
- [x] DRIFT_PROBE 상세 결과 JSON 저장 (`runner/experiment_runner.py`, `main.py`)
- [x] Harness Engineering (step4/5/6 DRIFT_PROBE 테스트) 구현

**다음 실험 목표:**
- [ ] 재실험: temperature=0.5 적용 후 Baseline이 다양한 결과를 내는지 확인
- [ ] LayeredMemory vs SemanticCompressor 차이 분석 (현재 동일)
- [ ] step6 0.0 붕괴 원인 분석 — DRIFT_PROBE 상세 결과 활용
- [ ] n=5 → n=10 이상으로 통계 신뢰도 확보
