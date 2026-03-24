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

## 🧪 실험 시나리오: StudentManager 진화

에이전트에게 `StudentManager` 클래스를 처음 작성하게 한 뒤, 4번의 수정 요청을 순서대로 내립니다. 수정이 거듭될수록 에이전트가 이전에 만든 기능을 망가뜨리거나 메서드 이름을 바꾸는 등 **의미 드리프트**가 발생할 가능성이 높아집니다.

### 초기 과제 — 기본 StudentManager 작성

에이전트가 처음 구현해야 하는 클래스입니다.

```python
class Student:
    name: str
    student_id: int

class StudentManager:
    def add_student(name, student_id)   # 학생 추가
    def get_student(student_id)         # 학생 조회
    def remove_student(student_id)      # 학생 삭제
```

---

### 수정 1 — 각 학생에게 점수 리스트 추가

**"각 학생에게 점수 리스트(scores: List[int])를 추가하고, add_score와 get_scores 메서드를 구현하세요."**

`Student` 데이터 구조에 `scores` 필드를 추가하고, `StudentManager`에 두 메서드를 붙이는 작업입니다.

```python
# Student에 추가되어야 하는 필드
scores: List[int] = []

# StudentManager에 추가되어야 하는 메서드
def add_score(student_id, score)    # 특정 학생의 점수 목록에 점수 1개 추가
def get_scores(student_id)          # 특정 학생의 전체 점수 목록 반환
```

**드리프트가 발생하는 상황 예시:** 에이전트가 기존 `add_student`, `get_student`, `remove_student`를 수정하거나 삭제하는 경우.

---

### 수정 2 — 평균 및 등급 계산 추가

```python
def get_average(student_id)   # 점수 리스트의 평균 반환
def get_grade(student_id)     # 평균에 따른 등급 반환
                              # A: 90+, B: 80+, C: 70+, D: 60+, F: 60미만
```

---

### 수정 3 — 파일 저장/로드 추가

```python
def save_to_file(filename)    # 전체 데이터를 JSON 파일로 저장
def load_from_file(filename)  # JSON 파일에서 데이터 로드
```

---

### 수정 4 — 타입 힌트 및 예외 처리 추가

기존 모든 메서드에 타입 힌트를 붙이고, 학생 미존재·파일 I/O 오류 등에 대한 예외 처리를 추가합니다. 기능 변경 없이 리팩토링만 수행해야 합니다.

---

### 드리프트율 계산 방법

각 단계마다 LLM이 코드를 0~10점으로 평가합니다.

```
드리프트율 = (초기 점수 - 최종 점수) / 초기 점수
```

값이 클수록 수정 과정에서 품질이 많이 떨어졌음을 의미합니다. `BaselineAgent`와 `StateDocAgent`의 드리프트율을 비교하여 상태 문서의 효과를 검증합니다.

---

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
