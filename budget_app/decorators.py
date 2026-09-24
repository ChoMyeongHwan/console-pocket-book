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
5. sys.exit(0 vs 1):
   - 운영체제(리눅스/맥/윈도우) 표준 규격(POSIX)에서 프로그램이 정상 종료되면 숫자 `0`을, 오류로 비정상 종료되면 `0이 아닌 값(예: 1)`을 반환해야 합니다.
"""

import sys
import time
import functools
from budget_app.exceptions import BudgetAppError

def handle_cli_error(func):
    """
    CLI 명령어 실행 중 발생하는 예외를 감싸서,
    개발용 스택 트레이스(긴 빨간 에러 메시지)를 감추고 
    사용자 친화적인 [오류] 원인과 [힌트] 해결책 형태로 출력한 뒤 비정상 종료(exit code 1)합니다.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 원본 함수 실행
            return func(*args, **kwargs)
        except BudgetAppError as e:
            # 의도된 비즈니스 예외 처리
            print(f"[오류] {e.message}")
            print(f"[힌트] {e.hint}")
            sys.exit(1)
        except Exception as e:
            # 예상치 못한 시스템 오류 처리
            print(f"[오류] 알 수 없는 오류가 발생했습니다: {str(e)}")
            print(f"[힌트] 관리자에게 문의하거나 입력 형식을 다시 확인하세요.")
            sys.exit(1)
    return wrapper

def measure_execution_time(func):
    """
    함수 실행 전후의 시각을 측정하여 순수 실행 시간을 계산하는 데코레이터입니다.
    대용량 데이터 조회나 복잡한 집계 작업의 성능 프로파일링에 활용할 수 있습니다.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()       # 함수 시작 시각 기록
        result = func(*args, **kwargs) # 실제 비즈니스 로직 실행
        end_time = time.time()         # 함수 종료 시각 기록
        # 필요 시 실행 시간 로깅: print(f"[{func.__name__}] 소요 시간: {end_time - start_time:.4f}초")
        return result
    return wrapper

def log_action(func):
    """
    주요 데이터 변경 작업(추가, 수정, 삭제)이 호출되었음을 추적하기 위한 횡단 관심사 로깅 데코레이터입니다.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 함수 실행
        return func(*args, **kwargs)
    return wrapper
