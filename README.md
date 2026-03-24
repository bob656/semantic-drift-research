# LLM 코딩 에이전트의 의미 드리프트 완화 연구

## 🎯 연구 목표
상태 문서(Spec.md, Plan.md, Constraints.md)를 유지하는 에이전트가 단순 컨텍스트 기반 에이전트보다 반복적인 코드 수정 과정에서 의미 드리프트를 더 효과적으로 완화하는지 검증합니다.

## 🖥️ 시스템 요구사항
- **실험 실행 컴퓨터**: Python 3.8+
- **Ollama 서버 컴퓨터**: Ollama 설치, qwen2.5-coder:7b 모델 (약 4.7GB), 18GB+ 메모리 권장
- 두 역할을 같은 컴퓨터에서 수행해도 됩니다.

## 🚀 실행 방법

### 1. Python 의존성 설치 (실험 실행 컴퓨터)
```bash
pip install -r requirements.txt
```

### 2. Ollama 서버 설정 (Ollama가 설치된 컴퓨터)
```bash
# Ollama 설치 (macOS)
brew install ollama

# 모델 다운로드
ollama pull qwen2.5-coder:7b

# 서버 시작 (외부 접속 허용)
OLLAMA_HOST=0.0.0.0 ollama serve
```

> 로컬에서 실행하는 경우 `brew services start ollama`로 백그라운드 시작해도 됩니다.

### 3. 실험 실행

**Ollama가 같은 컴퓨터에 있는 경우 (localhost)**
```bash
python main.py
```

**Ollama가 다른 컴퓨터에 있는 경우 (원격)**
```bash
python main.py --host http://<Ollama서버IP>:11434
```

**전체 옵션**
```bash
python main.py \
  --host http://192.168.0.10:11434 \   # Ollama 서버 주소
  --model qwen2.5-coder:7b \           # 사용할 모델
  --repeats 5                          # 반복 횟수 (통계 신뢰성, 권장: 5 이상)
```

### 4. 결과 확인
- 실험 중 터미널에 단계별 점수 및 드리프트율 실시간 출력
- 완료 후 `results/pilot_YYYYMMDD_HHMMSS.json`에 상세 결과 저장
- `experiment.log`에 실행 로그 저장

## 📁 프로젝트 구조
```
semantic-drift-research/
├── README.md
├── requirements.txt
├── main.py                      # 진입점, CLI 인자 처리
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # 공통 LLM 호출 로직
│   ├── baseline_agent.py        # 대화 히스토리 기반 에이전트
│   └── statedoc_agent.py        # 상태 문서(Spec/Plan/Constraints) 기반 에이전트
├── evaluator/
│   ├── __init__.py
│   └── code_evaluator.py        # LLM 기반 코드 품질 평가 (0-10점)
├── runner/
│   ├── __init__.py
│   └── experiment_runner.py     # 실험 시나리오 실행 및 결과 수집
├── analyzer/
│   ├── __init__.py
│   └── statistical_analyzer.py  # t-검정, Cohen's d 효과 크기 분석
└── results/
    └── .gitkeep
```
