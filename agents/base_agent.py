"""
base_agent.py — 모든 에이전트의 공통 기반 클래스

BaselineAgent와 StateDocAgent 모두 이 클래스를 상속합니다.
공통으로 필요한 두 가지 기능을 여기서 구현합니다:
  1. LLM 호출 (call_llm)
  2. 응답에서 코드 블록 추출 (extract_code)

실제 코드 생성/수정 전략은 서브클래스에서 각자 구현합니다.
"""
import ast
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class BaseAgent:
    """모든 에이전트의 기본 클래스"""

    def __init__(self, model: str, client: Any,
                 temperature: float = 0.5, max_tokens: int = 2048):
        """
        Parameters
        ----------
        model       : Ollama 모델 이름 (예: "qwen2.5-coder:7b")
        client      : ollama.Client 인스턴스 — 원격 서버 연결 정보를 담고 있음
        temperature : 출력 다양성 조절 (0.0=결정론적, 1.0=창의적)
                      0.5로 설정하여 실험 간 독립성 확보 (0.1은 너무 결정론적)
        max_tokens  : LLM이 한 번에 생성할 최대 토큰 수
        """
        self.model = model
        self.client = client
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 모든 LLM 호출 기록을 저장하는 리스트
        # 실험 후 JSON에 total_interactions 항목으로 저장됨
        self.interaction_log: List[Dict[str, Any]] = []

    def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Ollama 서버에 메시지를 보내고 응답 텍스트를 반환합니다.

        메시지 구조:
          [system]  → LLM의 역할/페르소나 설정 (선택)
          [user]    → 실제 요청 프롬프트

        호출 결과는 항상 interaction_log에 기록되며,
        오류 발생 시 "ERROR: ..." 문자열을 반환합니다 (예외를 밖으로 던지지 않음).
        """
        start_time = time.time()

        try:
            # system_prompt가 있을 때만 system 메시지를 포함
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,  # Ollama의 최대 생성 토큰 옵션명
                }
            )

            # Ollama 응답 구조: response['message']['content']
            result = response['message']['content']
            duration = time.time() - start_time

            # 로그에는 전체 내용 대신 미리보기만 저장 (메모리 절약)
            self.interaction_log.append({
                'timestamp': datetime.now().isoformat(),
                'prompt_preview': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                'system_preview': system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt,
                'response_preview': result[:300] + "..." if len(result) > 300 else result,
                'duration': duration,
                'success': True
            })

            return result

        except Exception as e:
            # 연결 실패, 모델 없음 등 → 실험이 멈추지 않도록 에러 문자열 반환
            duration = time.time() - start_time
            logger.error(f"LLM 호출 실패: {e}")

            self.interaction_log.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'duration': duration,
                'success': False
            })

            return f"ERROR: {str(e)}"

    def extract_code(self, response: str) -> str:
        """
        LLM 응답 텍스트에서 Python 코드 블록만 추출합니다.

        LLM은 보통 코드를 마크다운 코드 블록으로 감싸서 반환합니다:
          ```python
          def foo(): ...
          ```

        우선순위:
          1. ```python ... ``` 블록 (언어 명시된 경우)
          2. ``` ... ```       블록 (언어 미명시)
          3. 코드 블록 없으면 응답 전체를 그대로 반환

        주의: LLM이 닫는 ```를 생략하는 경우도 처리합니다.
              코드가 여전히 ``` 로 시작하면 fence를 강제 제거합니다.
        """
        text = response.strip()

        # 1순위: ```python 으로 시작하는 블록
        if "```python" in text:
            start = text.find("```python") + 9  # "```python" 길이 = 9
            end = text.find("```", start)        # 닫는 ```의 위치
            if end != -1:
                code = text[start:end].strip()
            else:
                # 닫는 ``` 없는 경우 — 열린 fence만 제거하고 나머지 전체 사용
                code = text[start:].strip()
        # 2순위: 언어 표시 없는 일반 코드 블록
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                code = text[start:end].strip()
            else:
                code = text[start:].strip()
        else:
            # 코드 블록이 아예 없는 경우 (LLM이 그냥 코드만 바로 쓴 경우)
            code = text

        # 안전장치: 추출 결과가 여전히 ``` 로 시작하면 강제 제거
        # (오염된 current_code가 프롬프트에 포함되어 중첩 fence가 생긴 경우)
        if code.startswith("```"):
            first_newline = code.find("\n")
            if first_newline != -1:
                code = code[first_newline + 1:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()

        return code

    def solve_initial(self, task: str) -> str:
        """
        초기 과제를 받아 코드를 처음 작성합니다.
        서브클래스(BaselineAgent, StateDocAgent)에서 반드시 구현해야 합니다.
        """
        raise NotImplementedError("서브클래스에서 구현해야 합니다")

    def modify_code(self, current_code: str, modification_request: str) -> str:
        """
        기존 코드에 수정 요청을 반영합니다.
        서브클래스(BaselineAgent, StateDocAgent)에서 반드시 구현해야 합니다.

        Parameters
        ----------
        current_code         : 이전 단계까지 완성된 코드
        modification_request : 이번 단계에서 추가/변경할 내용
        """
        raise NotImplementedError("서브클래스에서 구현해야 합니다")

    def modify_code_with_syntax_retry(self, current_code: str, modification_request: str,
                                       max_retries: int = 2) -> str:
        """
        modify_code를 실행하고 SyntaxError 발생 시 최대 max_retries회 재시도.

        재시도 시 수정 요청에 에러 내용과 교정 힌트를 추가해서 LLM이
        같은 실수를 반복하지 않도록 유도한다.

        Parameters
        ----------
        current_code         : 이전 단계까지 완성된 코드
        modification_request : 이번 단계 수정 요청
        max_retries          : 최대 재시도 횟수 (기본 2)
        """
        _SYNTAX_HINT = (
            "\n\n[이전 응답 오류] Python SyntaxError가 발생했습니다: {error}\n"
            "다음 사항을 반드시 지켜주세요:\n"
            "- ?.연산자는 Python에 없습니다. None 체크는 'if x is not None:' 을 사용하세요.\n"
            "- from dataclasses import dataclass, field 를 임포트하세요.\n"
            "- from enum import Enum 을 임포트하세요.\n"
            "- 완전한 Python 코드를 작성하세요."
        )

        request = modification_request
        for attempt in range(max_retries + 1):
            code = self.modify_code(current_code, request)
            try:
                ast.parse(code)
                if attempt > 0:
                    logger.info(f"SyntaxError 재시도 {attempt}회 만에 성공")
                return code
            except SyntaxError as e:
                if attempt < max_retries:
                    logger.warning(f"SyntaxError (시도 {attempt+1}/{max_retries+1}): {e}")
                    request = modification_request + _SYNTAX_HINT.format(error=str(e))
                else:
                    logger.warning(f"SyntaxError 재시도 {max_retries}회 소진, 마지막 결과 반환")

        return code

    def compress_code_for_context(self, code: str, max_body_lines: int = 4) -> str:
        """
        프롬프트 토큰을 줄이기 위해 현재 코드를 압축한다.

        전략: 시그니처·필드·docstring은 유지, 메서드 본문이 max_body_lines를
        초과하면 앞 max_body_lines 줄만 남기고 '# ... (생략)' 처리.

        LLM이 코드 구조(클래스·메서드 목록·타입)를 파악하기에 충분하면서
        입력 토큰을 크게 줄일 수 있다.

        Parameters
        ----------
        code           : 압축할 Python 코드 문자열
        max_body_lines : 메서드 본문 최대 허용 줄 수 (기본 6)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code  # 파싱 실패 시 원본 반환

        lines = code.splitlines()
        # 제거할 줄 번호 집합 (1-indexed)
        remove_lines = set()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # 본문 시작: def 줄 다음 줄부터
            body_start = node.lineno      # def 줄 (1-indexed)
            body_end   = node.end_lineno  # 마지막 줄 (inclusive)
            body_lines  = body_end - body_start  # def 줄 제외한 본문 길이

            if body_lines <= max_body_lines:
                continue

            # docstring 줄 수 계산 (보존)
            docstring_end = body_start  # def 줄
            if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                docstring_end = node.body[0].end_lineno

            # def 줄 + docstring 이후, max_body_lines 줄까지 보존
            keep_until = docstring_end + max_body_lines
            # keep_until ~ body_end-1 줄을 제거 (마지막 줄에 '# ...' 삽입)
            for ln in range(keep_until + 1, body_end):
                remove_lines.add(ln)

        if not remove_lines:
            return code

        result = []
        skip_next = False
        for i, line in enumerate(lines, start=1):
            if i in remove_lines:
                if not skip_next:
                    indent = len(line) - len(line.lstrip())
                    result.append(" " * indent + "# ... (생략)")
                    skip_next = True
            else:
                result.append(line)
                skip_next = False

        return "\n".join(result)
