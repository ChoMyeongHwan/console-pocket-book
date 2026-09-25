"""
[데이터 모델 정의 모듈 (models.py)]

💡 파이썬 기초 문법 설명:
1. dataclass (데이터 클래스):
   - 일반 파이썬 클래스는 객체를 만들 때 `def __init__(self, date, type, ...): self.date = date ...` 처럼
     반복적인 초기화 코드를 길게 작성해야 합니다.
   - `@dataclass` 데코레이터를 붙이면 파이썬이 생성자(`__init__`), 출력 포맷(`__repr__`), 
     객체 비교(`__eq__`) 메서드를 자동으로 만들어 줍니다.
2. 타입 힌트 (Type Hints):
   - `date: str`, `amount: int`, `tags: List[str]` 처럼 변수 뒤에 콜론(:)을 붙여 예상 타입을 명시합니다.
   - 파이썬은 동적 타입 언어이지만, 타입 힌트를 적어두면 IDE 자동완성이 활성화되고 
     코드의 의도와 계약(Contract)이 명확해져 협업과 유지보수에 매우 유리합니다.
3. field(default_factory=...):
   - 파이썬에서 리스트(`[]`)나 딕셔너리(`{}`) 같은 변경 가능한 객체(Mutable)를 함수의 기본값으로 직접 쓰면,
     모든 객체가 동일한 리스트 메모리를 공유해버리는 치명적인 버그가 발생합니다.
   - 이를 방지하기 위해 `default_factory=list`를 사용하여 "새 객체가 생성될 때마다 새로운 빈 리스트를 독립적으로 생성"하도록 지정합니다.
4. lambda (익명 함수):
   - 이름 없이 한 줄로 간단히 작성하는 일회용 함수입니다.
   - `lambda: f"TX-{uuid.uuid4().hex[:6].upper()}"`는 호출될 때마다 새로운 고유 ID 문자열을 반환합니다.
"""

from dataclasses import dataclass, field
from typing import List
import uuid

@dataclass
class Transaction:
    """
    [단일 거래 내역(수입/지출) 데이터 모델]
    - 핵심 책임: 
      1. 개별 거래의 상태(일자, 유형, 카테고리, 금액, 메모, 태그) 캡슐화
      2. 고유 식별자(ID: 'TX-XXXXXX')의 자동 채번 및 불변 식별성 보장
    - 불변 조건 (Invariants):
      - date: 반드시 유효한 YYYY-MM-DD 형식
      - type: 반드시 'income' 또는 'expense' 중 하나
      - amount: 반드시 0보다 큰 양의 정수 (amount > 0)
      - id: 객체 생성 시 1회 고유 채번되며 수정되지 않음
    """
    date: str                                       # 거래 일자 (YYYY-MM-DD 형식의 문자열)
    type: str                                       # 거래 유형 ('income' 또는 'expense')
    category: str                                   # 카테고리명 (예: food, salary)
    amount: int                                     # 금액 (양의 정수)
    memo: str = ""                                  # 메모 (선택 입력, 기본값은 빈 문자열)
    tags: List[str] = field(default_factory=list)   # 태그 목록 (예: ['외식', '점심'])
    # ID 생성 책임: uuid4 기반 16진수 6자리 난수를 생성하여 중복 없는 거래 식별자 부여
    id: str = field(default_factory=lambda: f"TX-{uuid.uuid4().hex[:6].upper()}")

@dataclass
class Category:
    """
    [가계부 카테고리 분류 데이터 모델]
    - 핵심 책임:
      1. 지출 및 수입 거래의 분류 체계 정의
      2. 시스템 기본 카테고리와 사용자 추가 카테고리의 구분을 통한 보호 정책 플래그 관리
    - 불변 조건 (Invariants):
      - name: 비어있지 않은 고유 문자열
      - is_default: True인 경우 시스템 기본 카테고리로 간주되어 삭제 불가
    """
    name: str                                       # 카테고리 이름 (예: food, transport)
    is_default: bool = False                        # 시스템 기본 제공 카테고리 여부 (기본값: False)

@dataclass
class Budget:
    """
    [월별 목표 지출 예산 데이터 모델]
    - 핵심 책임:
      1. 특정 월(YYYY-MM)에 대한 지출 한도 설정 상태 유지
      2. 월별 요약(summary) 시 예산 사용률 및 초과 여부 산출의 기준 데이터 제공
    - 불변 조건 (Invariants):
      - month: 반드시 YYYY-MM 형식
      - amount: 0보다 큰 양의 정수 (amount > 0)
    """
    month: str                                      # 대상 월 (YYYY-MM 형식의 문자열)
    amount: int                                     # 목표 예산 금액 (양의 정수)
