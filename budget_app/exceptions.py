"""
[사용자 정의 예외 클래스 모듈 (exceptions.py)]

💡 파이썬 기초 문법 설명:
1. 클래스 상속 (Inheritance):
   - `class BudgetAppError(Exception):` 처럼 괄호 안에 다른 클래스 이름을 넣으면, 
     부모 클래스(`Exception`)의 모든 특성과 기능을 물려받습니다.
   - 파이썬에서 에러를 직접 만들어 던지려면(`raise`) 반드시 파이썬의 표준 `Exception`을 상속해야 합니다.
2. super().__init__(message):
   - 자식 클래스에서 생성자(`__init__`)를 새로 정의할 때, 부모 클래스의 생성자도 함께 호출해주어야
     부모가 가진 기본 초기화 로직(예: 에러 메시지 보관)이 정상 동작합니다.
   - `super()`는 부모 클래스를 가리키는 특별한 키워드입니다.
3. pass 키워드:
   - 파이썬 문법상 클래스나 함수 내부에는 최소 한 줄 이상의 실행 코드가 있어야 합니다.
   - 부모 클래스의 기능을 그대로 사용하고 추가로 작성할 코드가 없을 때, 
     아무 일도 하지 않는 빈 문장인 `pass`를 적어 문법 오류를 방지합니다.
4. 왜 커스텀 예외를 계층적으로 만드는가?
   - 유효성 검증 실패(`ValidationError`), 리소스 없음(`NotFoundError`) 등을 각각 정의해두면,
     최상위 데코레이터에서 `except BudgetAppError:` 한 줄로 모든 비즈니스 예외를 우아하게 잡아낼 수 있습니다.
"""

class BudgetAppError(Exception):
    """
    애플리케이션 최상위 비즈니스 예외 클래스.
    모든 커스텀 예외는 이 클래스를 상속받습니다.
    """
    def __init__(self, message: str, hint: str):
        super().__init__(message)   # 파이썬 표준 Exception에 오류 메시지 등록
        self.message = message      # 사용자에게 노출할 오류의 직접적인 원인
        self.hint = hint            # 사용자가 해결할 수 있는 힌트 안내 문구

class ValidationError(BudgetAppError):
    """날짜 형식 오류, 금액 음수 입력, 미등록 카테고리 등 입력값 유효성 검증 실패 시 발생"""
    pass

class DataStoreError(BudgetAppError):
    """파일 I/O, 디렉터리 접근 등 데이터 저장소 처리 중 오류 발생 시 사용"""
    pass

class NotFoundError(BudgetAppError):
    """수정/삭제하려는 거래 ID나 카테고리 파일 등을 찾을 수 없을 때 발생"""
    pass
