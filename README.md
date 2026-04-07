# LLM 코딩 에이전트의 의미 드리프트 연구

## 연구 요약

LLM 기반 코딩 에이전트가 소프트웨어를 반복적으로 수정하는 과정에서 이전에 구현한 기능을 잃어가는 현상(**의미 드리프트, Semantic Drift**)을 측정하고, 어떤 조건에서 컨텍스트 관리 전략이 이를 완화하는지 규명한다.

**주요 발견:**
- 구조적 컨텍스트 관리(상태 문서, 요약)는 단순 대화 이력보다 일관되게 나은 결과를 보이지 않는다
- 핵심 조건: 의미론적 계약(타입, 상태, 메서드 의존성)이 **항상 최신 상태**여야 한다. 낡은 계약은 오히려 LLM을 잘못 안내한다
- DRIFT_PROBE 하네스로 어느 단계에서 어떤 계약이 깨지는지 기계적으로 측정 가능함을 보인다

---

## 실험 설계

### 시나리오: OrderSystem Evolution (7단계, 충돌 유발형)

각 수정이 이전 단계의 구현 방식을 의도적으로 변경하도록 설계:

| 단계 | 수정 내용 | 충돌 유발 요소 |
|---|---|---|
| step0 | OrderManager 초기 구현 | — |
| step1 | Item dataclass 도입 | items: List[str] → List[Item], total 자동계산 |
| step2 | 할인 시스템 | discount_percent(0.0~1.0), total 계산 변경 |
| step3 | 상태 머신 | cancel_order: 삭제→CANCELLED 상태 전환 |
| step4 | 결제 통합 | process_payment + confirm_order 역할 충돌 |
| step5 | 재고 관리 | Inventory 클래스, add_order 시그니처 변경 |
| step6 | 주문 이력 | created_at(datetime) 추가, get_order_history |

### 평가 방식

- **exec 모드**: 코드를 직접 실행하여 테스트 통과율(0~10점)로 채점
- **DRIFT_PROBE**: step N에서 step K(K≪N)의 계약 보존 여부를 직접 검증하는 테스트
- **드리프트 지표**: `scores[0] - min(scores)` (절대 하락량, 0~10점 척도)

### 비교 에이전트

| 에이전트 | 전략 | 파일 |
|---|---|---|
| **Baseline** | 최근 6개 대화 이력, 코드 300자 절단 | `agents/baseline_agent.py` |
| **LayeredMemory** | Layer1(영구 AST 인터페이스) + Layer2(Delta 이력) + Layer3(현재 코드) | `agents/layered_memory_agent.py` |
| **SemanticCompressor** | AST 타입계약 + 상태전이 + 메서드의존성, step0 기준 불변 | `agents/semantic_compressor_agent.py` |
| **SemanticCompressorV2** | SemanticCompressor + 매 수정마다 계약 갱신 | `agents/semantic_compressor_agent.py` |

---

## 실험 결과 요약

### Phase 1~5 (2026-03-24 ~ 03-31): 가설 검증 시도

| 전략 | Baseline 대비 | 원인 |
|---|---|---|
| StateDoc (Spec+Plan+Constraints) | 더 나쁨 (p=0.041, d=-1.54) | LLM이 추상 문서에서 타입 재해석 (hallucination) |
| CoTDoc-LLM | 더 나쁨 (p>0.34) | Lost in the Middle + hallucination |
| CoTDoc-AST | 더 나쁨 (p=0.172) | AST로 hallucination 제거했으나 의미적 계약 미흡 |

**결론:** "구조적 문서가 항상 낫다"는 원래 가설은 기각됨

### Phase 6~8 (2026-04-01 ~ 현재): 원인 분석

**진단 실험 (diagnose_step6.py):**

step5 완성 코드를 직접 주고 step6만 요청했을 때:

| 에이전트 | 점수 |
|---|---|
| Baseline | 0.0 (timeout) |
| LayeredMemory | 0.0 (timeout) |
| SemanticCompressor | **10.0** (DRIFT_PROBE 5/5) |

→ 생성 능력 한계가 아니라 **프롬프트 구조 문제**

**핵심 발견:**
1. step0에서 추출한 계약이 step6에서 낡음 → Inventory, Payment 등 누락 → 잘못된 가이드
2. 계약 갱신 시 깨진 코드에서 추출하면 오염이 다음 단계로 전파됨 (contamination cascading)
3. SemanticCompressorV2(매 단계 계약 갱신 + 원본 클래스 검증)가 해결책으로 제안됨

---

## 실행 방법

### 환경 설정

```bash
# Ollama 서버 (원격 컴퓨터)
OLLAMA_HOST=0.0.0.0 ollama serve
ollama pull qwen2.5-coder:14b

# 실험 실행
conda activate python312rg
```

### 전체 실험

```bash
# 4개 에이전트 전체 비교 (3~5시간)
python main.py --host http://192.168.100.52:11434 --eval-mode exec --repeats 5
```

### 빠른 검증 (step3~6만 실행)

```bash
# 전체 에이전트, step3~6만 (~40분)
python main.py --host http://192.168.100.52:11434 --eval-mode exec --repeats 1 --quick

# 특정 에이전트만 (~10~15분)
python main.py --host http://192.168.100.52:11434 --eval-mode exec --repeats 1 \
  --quick --agents Baseline,SemanticCompressorV2
```

### 붕괴 원인 진단

```bash
python diagnose_step6.py
```

---

## 프로젝트 구조

```
semantic-drift-research/
├── main.py                          # 진입점 (--quick, --agents 지원)
├── diagnose_step6.py                # step6 붕괴 원인 진단 스크립트
├── agents/
│   ├── base_agent.py                # LLM 호출, extract_code 공통 로직
│   ├── baseline_agent.py            # 대화 이력 기반 (Control)
│   ├── layered_memory_agent.py      # 3계층 메모리
│   └── semantic_compressor_agent.py # SemanticCompressor + V2
├── evaluator/
│   ├── code_executor.py             # exec 모드 테스트 (DRIFT_PROBE 포함)
│   └── code_evaluator.py            # LLM 채점 (llm 모드)
├── runner/
│   └── experiment_runner.py         # 실험 루프, quick 모드
├── analyzer/
│   └── statistical_analyzer.py      # t-검정, Cohen's d
└── results/
    ├── abstract.md                  # 연구 초록 (한국어/영어)
    ├── research_log.md              # 전체 실험 이력 및 설계 결정
    └── pilot_*.json                 # 실험 결과 (27개)
```

---

## 참고 논문

| 논문 | 반영 위치 |
|---|---|
| Lost in the Middle (Liu et al., TACL 2024) | 계약을 프롬프트 맨 앞 배치 |
| LLMLingua (Jiang et al., EMNLP 2023) | LLM 요약 → AST 추출 |
| MemGPT (Packer et al., 2023) | 계층적 메모리 구조 설계 |
| SWE-Bench-CL (Wu et al., 2025) | 코딩 에이전트 continual learning 벤치마크 |
| SWE-EVO (Dang et al., 2025) | 장기 소프트웨어 진화 벤치마크 |
| Broken Telephone (Mohamed et al., ACL 2025) | 반복 생성에서 정보 왜곡 이론적 배경 |
