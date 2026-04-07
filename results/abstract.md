# 반복 코드 수정 과정에서 LLM 코딩 에이전트의 의미 드리프트 측정 및 완화

> 작성일: 2026-04-07  
> 저자: Wonho Choi

---

## 초록 (Abstract)

대규모 언어 모델(LLM) 기반 코딩 에이전트는 소프트웨어를 반복적으로 수정하는 과정에서 이전에 구현된 기능을 점진적으로 상실하는 현상이 관찰된다. 본 연구는 이 현상을 **의미 드리프트(Semantic Drift)**로 정의하고, 구조적 컨텍스트 관리 전략이 드리프트를 완화한다는 가설을 실증적으로 검증한다.

**실험 설계.** OrderManager 시스템의 7단계 충돌 유발형 진화 시나리오를 설계하였다. 각 수정은 이전 단계의 구현 방식을 의도적으로 변경한다(Item 타입 도입 → 할인 시스템 → 상태 머신 → 결제 통합 → 재고 관리 → 주문 이력). LLM 채점이 코드 변화를 감지하지 못하는 한계를 극복하기 위해 코드를 직접 실행하는 exec 평가 방식을 채택하였다. 드리프트는 초기 점수에서 최솟값을 뺀 절대 하락량(0~10점)으로 측정한다.

**비교 에이전트.** (1) **Baseline**: 최근 대화 이력만 사용하는 제어 집단. (2) **LayeredMemory**: AST 추출 영구 인터페이스, Delta 이력, 현재 코드의 3계층 구조. (3) **SemanticCompressor**: 타입 계약, 상태 전이 규칙, 메서드 간 의존성을 step0에서 추출하여 프롬프트 앞에 고정 배치. (4) **SemanticCompressorV2**: 매 수정 후 계약을 최신 코드 기준으로 갱신하는 메커니즘 추가.

**주요 발견.** 첫째, 상태 문서, LLM 요약, AST 요약 등 기존에 제안된 구조적 전략은 모두 Baseline보다 나쁘거나 동등한 결과를 보였다. 이는 원래 가설의 기각을 의미하며, 단순히 "구조를 추가하면 된다"는 직관이 틀렸음을 시사한다. 둘째, 원인을 규명하기 위한 진단 실험에서, step0 기준으로 추출된 계약이 6단계 수정 후 낡아 잘못된 가이드를 제공하는 반면, 최신 계약을 직접 주입하면 SemanticCompressor가 step6에서 10/10을 달성하였다. 이는 드리프트가 생성 능력 한계가 아닌 **계약 신선도(contract freshness) 문제**임을 보인다. 셋째, 계약 갱신 시 오염된 중간 코드에서 잘못된 계약이 추출되어 후속 단계로 전파되는 **오염 누적(contamination cascading)** 현상이 관찰되었다. 넷째, 제안한 **DRIFT_PROBE 하네스**는 어느 단계에서 어떤 계약이 깨지는지를 기계적으로 측정하여, 기존 연구(SWE-EVO, SWE-Bench-CL)의 최종 통과율 지표보다 드리프트 원인을 정밀하게 진단한다.

**한계.** 본 연구는 단일 시나리오, 단일 모델(qwen2.5-coder:14b)에서 예비 실험 수준으로 수행되었으며, 통계적 유의성 확보(n≥30)와 다중 도메인 검증은 후속 연구로 남긴다.

**키워드:** LLM 코딩 에이전트, 의미 드리프트, 컨텍스트 관리, 의미론적 계약, 계약 신선도, AST 정적 분석

---

## Abstract (English)

LLM-based coding agents progressively lose previously implemented functionality during iterative code modification — a phenomenon we term **semantic drift**. We empirically test the hypothesis that structured context management mitigates drift, and find that it does not hold unconditionally.

**Experimental Setup.** We design a 7-step conflict-inducing evolution scenario for an OrderManager system, where each modification intentionally challenges prior implementation decisions. We use executable test-based evaluation (exec mode) rather than LLM scoring, which we show fails to detect code degradation. Drift is the absolute score drop from the initial step to the minimum, removing dependency on initial score magnitude.

**Agents.** We compare four agents: (1) **Baseline**, a sliding-window conversation history agent; (2) **LayeredMemory**, a three-layer structure (permanent AST interface, semantic delta log, current code); (3) **SemanticCompressor**, placing AST-extracted type contracts, state transition rules, and cross-method dependencies at the prompt's beginning; and (4) **SemanticCompressorV2**, adding per-step contract refresh.

**Key Findings.** All structured strategies tested prior to SemanticCompressorV2 — state documents, LLM summaries, AST summaries — performed no better than or worse than Baseline, rejecting the original hypothesis. A diagnostic experiment reveals the underlying cause: contracts extracted at step 0 become **stale** by step 6, omitting structures added in subsequent steps (Inventory, Payment). When fresh contracts are injected directly, SemanticCompressor achieves 10/10 on step 6 while Baseline and LayeredMemory time out on identical input, demonstrating that drift is a **contract freshness problem** rather than a generation capability limit. We additionally identify **contamination cascading**, where contracts extracted from corrupted intermediate code propagate errors forward, and propose original class membership validation as a mitigation. Our **DRIFT_PROBE harness** enables mechanistic diagnosis of which contracts break at which step, providing finer granularity than the final pass rates reported in SWE-EVO and SWE-Bench-CL.

**Limitations.** This is a preliminary study using a single scenario and model (qwen2.5-coder:14b). Statistical significance (n≥30) and multi-domain validation are left for future work.

**Keywords:** LLM coding agents, semantic drift, context management, behavioral contracts, contract freshness, AST static analysis

---

## 연구 현황 (2026-04-07 기준)

| 항목 | 내용 |
|---|---|
| 실험 단계 | Phase 8 진행 중 — SemanticCompressorV2 검증 실험 |
| 사용 모델 | qwen2.5-coder:14b (Ollama, 로컬 서버) |
| 평가 방식 | exec 모드 (코드 실행 테스트) |
| 반복 횟수 | 목표 n=5 (현재 n=1~3으로 검증 중) |
| 주요 미결 | SemanticV2 계약 갱신 안정성 검증, 전체 4개 에이전트 통계 비교 |

---

## 참고 문헌

- Liu et al. (2024). Lost in the Middle: How Language Models Use Long Contexts. *TACL*. arXiv:2307.03172
- Jiang et al. (2023). LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models. *EMNLP 2023*. arXiv:2310.06839
- Packer et al. (2023). MemGPT: Towards LLMs as Operating Systems. arXiv:2310.08560
- Wu et al. (2025). SWE-Bench-CL: Continual Learning for Coding Agents. arXiv:2507.00014
- Dang et al. (2025). SWE-EVO: Benchmarking Coding Agents in Long-Horizon Software Evolution Scenarios. arXiv:2512.18470
- Mohamed et al. (2025). LLM as a Broken Telephone: Iterative Generation Distorts Information. *ACL 2025*. arXiv:2502.20258
- Adams et al. (2023). From Sparse to Dense: GPT-4 Summarization with Chain of Density Prompting. arXiv:2309.04269
