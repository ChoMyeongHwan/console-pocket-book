import sys
import time
import functools
from budget_app.exceptions import BudgetAppError

def handle_cli_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BudgetAppError as e:
            print(f"[오류] {e.message}")
            print(f"[힌트] {e.hint}")
            sys.exit(1)
        except Exception as e:
            print(f"[오류] 알 수 없는 오류가 발생했습니다: {str(e)}")
            print(f"[힌트] 관리자에게 문의하세요.")
            sys.exit(1)
    return wrapper

def measure_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        # print(f"[{func.__name__}] 실행 시간: {end - start:.4f}초")
        return result
    return wrapper

def log_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Could log somewhere if we wanted
        return func(*args, **kwargs)
    return wrapper
