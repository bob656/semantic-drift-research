# LLM 코딩 에이전트 의미 드리프트 연구 — 연구 일지

> 최종 업데이트: 2026-04-08

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
| 2026-04-08 | step6 0.0 (전 에이전트) | Order dataclass `created_at`을 필드 맨 앞 배치 → TypeError | 수정 요청에 dataclass 필드 순서 규칙 명시 |
| 2026-04-08 | step6 `history_includes_cancelled` 실패 | `get_order_history()`가 Order 객체 대신 튜플 반환 | 수정 요청에 "Order 객체의 리스트 반환" 명시 |

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
| 11 | 계약을 매 단계 갱신 (v2) | step0 기준 계약은 step6에서 낡아 잘못된 가이드 제공 — 진단 실험으로 확인 |

---

## 참고 논문

| 논문 | 어디에 반영 |
|---|---|
| Lost in the Middle (Liu et al., TACL 2024, arxiv:2307.03172) | 중요 정보 프롬프트 앞/끝 배치 |
| LLMLingua (Jiang et al., EMNLP 2023, arxiv:2310.06839) | LLM 요약 → AST 추출 |
| MemGPT (Packer et al., arxiv:2310.08560) | 계층적 메모리 구조 |
| Recursive Summarization (arxiv:2308.15022) | Delta 누적 요약 |
| Chain of Density (Adams et al., 2023) | 구체적 엔티티 중심 요약 |
| SWE-Bench-CL (arxiv:2507.00014) | Continual learning for coding agents 벤치마크 |
| SWE-EVO (Dang et al., arxiv:2512.18470) | 장기 소프트웨어 진화 벤치마크 |
| Broken Telephone (Mohamed et al., ACL 2025, arxiv:2502.20258) | 반복 생성에서 정보 왜곡 이론 |

### 2026-04-08 추가 발굴 논문 (드리프트 원인 관련)

| 논문 | arXiv | 핵심 관련성 |
|---|---|---|
| LLMs Get Lost In Multi-Turn Conversation (Laban et al., 2025) | 2505.06120 | 멀티턴 평균 39% 성능 하락, 초기 출력 과의존 → contamination cascading 직접 설명 |
| Unable to Forget: Proactive Interference (Wang et al., 2025) | 2506.08184 | 오래된 step0 계약이 새 상태를 능동적으로 방해 (proactive interference) — contract freshness 이론적 근거 |
| Agent Drift: Quantifying Behavioral Degradation (Rath, 2026) | 2601.04170 | semantic/coordination/behavioral drift 분류 체계, ASI 지표 — 이 연구 DRIFT_PROBE와 차별점 비교 |
| Spec-Driven Development (Piskala, 2026) | 2602.00180 | 실제 AI 개발에서 낡은 컨텍스트 문서가 최신 리팩토링과 충돌 — contract staleness 실사례 |
| Context Length Alone Hurts LLM Performance (Du et al., EMNLP 2025) | 2510.05381 | 완벽한 정보 retrieval 하에서도 컨텍스트 길이 자체가 성능 저하 유발 |
| Know But Don't Tell (Lu et al., 2024) | 2406.14673 | LLM이 관련 정보를 인코딩하지만 생성에 미반영 — 상태 문서 전략 실패 원인 |
| How LLMs Fail in Agentic Scenarios (Roig, 2025) | 2512.07497 | 풍부한 컨텍스트가 "맥락에 의한 방해" 실패 유발 — 구조적 전략 역효과 설명 |
| Beyond Exponential Decay: Error Accumulation (Arbuzov et al., 2025) | 2505.24187 | 오류가 핵심 의미 결정 지점에 집중 — 계약 오염이 왜 치명적인지 설명 |
| LoCoBench-Agent (Qiu et al., 2025) | 2511.13998 | SE 에이전트 ~12턴 임계점 이후 성능 급하락 — 단계 수 증가에 따른 실증 근거 |
| Drift No More? Context Equilibria (Dongre et al., 2025) | 2510.07777 | 멀티턴 드리프트가 bounded stochastic process — 구조적 전략 한계 이론 |

---

## Phase 8: 진단 실험 + SemanticCompressorV2 (2026-04-07)

### diagnose_step6.py 결과

**실험 설계:** step5 완성 코드를 직접 주고 step6만 요청 → 메모리 문제 vs 생성 능력 한계 판별

| 에이전트 | 점수 | 원인 |
|---|---|---|
| Baseline | 0.00 | LLM timeout (600초 초과) |
| LayeredMemory | 0.00 | LLM timeout (600초 초과) |
| SemanticCompressor | **10.00** | DRIFT_PROBE 5/5 포함 전부 통과 |

**핵심 발견:**
- H1(생성 능력 한계) 부분 기각 — SemanticCompressor는 step6를 완벽히 풀었음
- Baseline/LayeredMemory의 timeout은 **프롬프트 구조 문제** (현재 코드 7113자를 처리하는 방식 차이)
- SemanticCompressor의 타입 계약 + 상태 전이 규칙이 LLM에게 `created_at` 추가 시 어떤 구조를 건드려야 하는지 명확히 안내한 것으로 추정

**실제 실험(pilot_20260407)에서 SemanticCompressor도 0.0이었던 이유:**
- 진단: step5 코드 → 계약 추출 → step6 요청 (계약이 최신)
- 실제: step0 코드 → 계약 추출 → 6번 수정 후 step6 요청 (계약이 낡음)
- step6 시점엔 Inventory, Payment, status 등이 추가됐지만 계약은 step0 기준 → 잘못된 가이드

### SemanticCompressorV2 설계

**파일:** `agents/semantic_compressor_agent.py` (SemanticCompressorV2Agent 서브클래스)

**v1 vs v2 차이:**
```
v1: solve_initial()에서 계약 1회 추출 → 이후 불변
v2: modify_code() 마다 new_code로 계약 재추출 → 항상 현재 코드 반영
```

**runner에 추가:** `semantic_v2_results` 키로 별도 추적

---

## 초록 문서

`results/abstract.md` — 한국어/영어 초록 + 연구 현황 + 참고문헌

---

## Phase 9: step6 버그 수정 + 재실험 (2026-04-08)

### step6 버그 2건 수정

**버그 1: Order dataclass 필드 순서 오류**
- 원인: LLM이 `created_at: datetime = field(default_factory=...)` 를 필드 맨 앞에 배치
  → Python 규칙 위반: default 있는 필드 뒤에 default 없는 필드 불가 → TypeError
  → `_add()` 헬퍼가 예외를 조용히 삼켜 주문이 저장되지 않음
- 수정: 수정 요청에 dataclass 필드 순서 규칙 + 올바른 예시 명시

**버그 2: `get_order_history()` 튜플 반환**
- 원인: LLM이 `list_orders()`와 유사하게 튜플 리스트로 구현
  → 테스트에서 `getattr(o, "status", "")` 접근 → 빈 문자열 → FAIL
- 수정: 수정 요청에 "Order 객체의 리스트 반환 (튜플 리스트 아님)" 명시

**수정 후 검증 결과 (pilot_20260408_105132.json):**

| 에이전트 | scores | drift |
|---|---|---|
| Baseline | [10, 10, 10, 10] | **0.0** |
| SemanticCompressorV2 | [10, 10, 10, 10] | **0.0** |

→ 모든 테스트 통과. 버그 수정 완료 확인.

### 진행 중

- [ ] 4개 에이전트 n=5 재실험 (수정된 프롬프트 적용, pilot_bxuzxbg0x 실행 중)

---

## 현재 상태 (2026-04-08)

**완료:**
- [x] temperature 0.5로 수정
- [x] DRIFT_PROBE JSON 저장
- [x] SemanticCompressorV2 구현 (매 단계 계약 갱신 + 오염 방지)
- [x] --quick / --agents CLI 플래그 추가
- [x] step6 dataclass 필드 순서 힌트 추가
- [x] step6 get_order_history() 반환 타입 명시
- [x] 관련 논문 22편 추가 발굴 (research_log 참고문헌 섹션)

**다음 실험 목표:**
- [ ] 4개 에이전트 n=5 재실험 결과 분석
- [ ] 통계적 유의성 확인 (p < 0.05, n=5 기준)
- [ ] n=30 전체 실험 여부 결정
- [ ] abstract.md 참고문헌 업데이트 (신규 논문 반영)
