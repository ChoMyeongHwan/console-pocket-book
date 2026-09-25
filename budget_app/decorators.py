"""
[공통 관심사 데코레이터 모듈 (decorators.py)]

💡 파이썬 기초 문법 설명:
1. 일급 객체 (First-Class Citizen)와 함수 전달:
   - 파이썬에서는 함수도 하나의 값(객체)으로 취급되어, 다른 함수의 인자로 전달하거나 함수 안에서 또 다른 함수를 만들어 반환할 수 있습니다.
2. 데코레이터 (Decorator) 패턴:
   - 기존 함수의 소스코드를 수정하지 않고, 함수의 앞/뒤에 추가 작업(로깅, 실행 시간 측정, 예외 처리 등)을 덧붙이는 기법입니다.
   - `@handle_cli_error` 문법은 사실 `main = handle_cli_error(main)`과 정확히 동일한 동작을 하는 '문법적 설탕(Syntactic Sugar)'입니다.
3. *args 와 **kwargs (가변 인자):
   - `*args`: 함수에 몇 개가 들어올지 모르는 위치 인자(Positional arguments)들을 튜플(tuple) 형태로 한꺼번에 받습니다.
   - `**kwargs`: `name="홍길동"`, `age=20` 같은 키워드 인자(Keyword arguments)들을 딕셔너리(dict) 형태로 한꺼번에 받습니다.
   - 덕분에 어떤 인자 구성을 가진 함수라도 원형 그대로 감쌀(wrap) 수 있습니다.
4. @functools.wraps:
   - 데코레이터로 함수를 감싸면, 원본 함수의 이름(`__name__`)이나 설명 문서(`__doc__`)가 wrapper 함수로 덮어씌워져 사라집니다.
   - `@functools.wraps(func)`를 붙여주면 원본 함수의 메타데이터를 보존해 디버깅과 문서화에 문제가 생기지 않도록 해줍니다.
5. 세분화된 POSIX exit code:
   - 운영체제 표준 규격에 따라 정상 종료는 0, 에러 발생 시 에러 성격에 따른 고유 종료 코드(1: 일반 오류, 2: 유효성 검증 오류, 3: 리소스 미존재 오류, 4: 저장소 오류)를 반환합니다.
6. 개발용/운영용 디버그 토글:
   - CLI 인자 `--debug` 또는 환경변수 `BUDGET_APP_DEBUG=1`을 감지하여 개발 환경에서는 상세 스택트레이스를 출력하고, 운영 환경에서는 사용자 친화적 메시지만 노출합니다.
"""

import os
import sys
import time
import functools
import traceback
from typing import Callable, Any
from budget_app.exceptions import BudgetAppError

def is_debug_mode() -> bool:
    """CLI 옵션 --debug 또는 환경변수 BUDGET_APP_DEBUG=1 활성화 여부 확인"""
    return "--debug" in sys.argv or os.environ.get("BUDGET_APP_DEBUG") == "1"

def handle_cli_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    [데코레이터: 예외 처리 및 POSIX 종료 코드 제어]
    - 동작: CLI 명령어 실행 중 발생하는 예외를 가로채어 스택트레이스를 은닉하고 [오류]/[힌트]를 출력합니다.
    - 부작용(Side Effect): 오류 발생 시 프로세스를 exit_code(2, 3, 4, 1)로 강제 종료(sys.exit)합니다.
    - 디버그 모드: --debug 플래그 활성화 시 상세 스택트레이스를 추가 출력합니다.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except BudgetAppError as e:
            print(f"[오류] {e.message}")
            print(f"[힌트] {e.hint}")
            if is_debug_mode():
                print(f"[디버그 정보] 예외 클래스: {e.__class__.__name__}, 할당된 종료 코드: {e.exit_code}")
                traceback.print_exc()
            sys.exit(e.exit_code)
        except Exception as e:
            print(f"[오류] 알 수 없는 오류가 발생했습니다: {str(e)}")
            print(f"[힌트] 관리자에게 문의하거나 --debug 옵션으로 상세 오류를 확인하세요.")
            if is_debug_mode():
                print("[디버그 정보] 미처리 내부 스택트레이스:")
                traceback.print_exc()
            sys.exit(1)
    return wrapper

def measure_execution_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    [데코레이터: 성능 프로파일링 및 실행 시간 측정]
    - 동작: 대상 함수의 호출 시점부터 완료 시점까지의 경과 시간을 초 단위로 정밀 측정합니다.
    - 부작용(Side Effect): 환경변수 BUDGET_APP_PROFILE=1 활성화 시 표준 에러(stderr)에 소요 시간을 출력합니다.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        if os.environ.get("BUDGET_APP_PROFILE") == "1" or is_debug_mode():
            sys.stderr.write(f"[성능 측정] {func.__name__} 소요 시간: {duration:.4f}초\n")
        return result
    return wrapper

def log_action(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    [데코레이터: 비즈니스 감사(Audit) 로깅]
    - 동작: 거래/카테고리/예산의 생성·수정·삭제 등 주요 상태 변경 메서드 호출 이벤트를 감지합니다.
    - 부작용(Side Effect): 환경변수 BUDGET_APP_AUDIT=1 활성화 시 호출된 함수명과 파라미터를 audit 로그 스트림에 기록합니다.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if os.environ.get("BUDGET_APP_AUDIT") == "1":
            sys.stderr.write(f"[감사 로그] 메서드 실행: {func.__name__}, 호출 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        return func(*args, **kwargs)
    return wrapper
