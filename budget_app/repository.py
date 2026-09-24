"""
[영구 저장소 모듈 (repository.py)]

💡 파이썬 기초 문법 및 아키텍처 설명:
1. Generator (제너레이터)와 yield 키워드:
   - 일반 함수는 `return`을 만나면 모든 계산 결과를 메모리에 한꺼번에 올려서 반환하고 종료됩니다.
     (예: 100만 줄의 파일을 `f.readlines()`로 읽으면 수백 MB의 RAM을 일시에 점유)
   - `yield` 키워드를 사용하면 함수가 실행 도중 값을 '하나씩 건네주고 그 자리에서 일시 정지(Pause)'합니다.
     호출하는 쪽에서 `for item in generator:`로 다음 값을 요구할 때 비로소 다음 줄을 읽으므로,
     아무리 거대한 파일도 단 한 줄 분량의 메모리(O(1) 공간 복잡도)만 사용하여 스트리밍 처리할 수 있습니다.
2. Context Manager (컨텍스트 매니저 - with 문):
   - `with open(...) as f:` 구문은 파일 열기 작업 후 블록을 벗어날 때, 
     에러가 발생하더라도 자동으로 `f.close()`를 호출해 시스템 자원 누수(Leak)를 원천 차단합니다.
3. 딕셔너리 언패킹 (Dictionary Unpacking - **data):
   - `Transaction(**data)`는 딕셔너리의 키-값 쌍(`{"date": "...", "amount": 1000}`)을
     함수의 인자(`date="...", amount=1000`)로 자동으로 풀어헤쳐 전달하는 편리한 문법입니다.
4. 리스트 컴프리헨션 (List Comprehension):
   - `[t.__dict__ for t in transactions]`는 for 루프를 한 줄로 축약하여 새로운 리스트를 생성하는 파이썬 고유의 우아한 문법입니다.
5. 원자적 파일 교체 (Atomic File Replace):
   - 원본 파일에 직접 쓰기(`write`)를 진행하다가 프로그램이 강제 종료되면 원본 파일이 손상(Corrupted)됩니다.
   - `tempfile.mkstemp`로 임시 파일에 데이터를 완벽히 기록한 뒤, OS 수준의 원자적 연산인 `os.replace`로 순식간에 이름을 변경하여 데이터 무결성을 보장합니다.
"""

import os
import json
import tempfile
from typing import Generator, List, Any, Dict
from budget_app.models import Transaction, Category, Budget

# 프로그램 최초 실행 시 자동 생성할 기본 카테고리 목록
DEFAULT_CATEGORIES = [
    "food", "transport", "living", "salary", "entertainment", "shopping", "medical", "etc"
]

class Repository:
    """
    JSONL 포맷 파일을 기반으로 데이터를 영구 보관하고,
    제너레이터를 통해 대용량 데이터를 메모리 효율적으로 스트리밍 제공하는 저장소 클래스입니다.
    """
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        # 분리 저장할 3개 이상의 핵심 파일 경로 설정
        self.transactions_path = os.path.join(data_dir, "transactions.jsonl")
        self.categories_path = os.path.join(data_dir, "categories.jsonl")
        self.budgets_path = os.path.join(data_dir, "budgets.jsonl")
        
        # 디렉터리 및 초기 기본 카테고리 시드 자동 설정
        self._init_dir()
        self._init_categories()
        
    def _init_dir(self):
        """데이터 저장 폴더가 없으면 새로 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _init_categories(self):
        """카테고리 파일이 없으면 기본 8개 카테고리를 영구 저장소에 자동 등록"""
        if not os.path.exists(self.categories_path):
            self.save_categories([Category(name=c, is_default=True) for c in DEFAULT_CATEGORIES])

    def _read_jsonl(self, path: str) -> Generator[Dict[str, Any], None, None]:
        """
        JSONL 파일을 한 줄씩 읽어 파싱하는 yield 기반 제너레이터 함수.
        대용량 파일도 전체를 메모리에 올리지 않고 한 줄씩 스트리밍 처리합니다.
        """
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # JSON 문자열을 파이썬 딕셔너리로 변환 후 호출자에게 1개씩 양보(yield)
                    yield json.loads(line)

    def _write_jsonl_atomic(self, path: str, items: List[Dict[str, Any]]):
        """
        데이터 안정성을 위한 원자적 파일 쓰기:
        임시 파일에 모든 데이터를 기록한 뒤 원본 파일로 원자적 교체(rename)를 수행합니다.
        """
        # 동일 디렉터리 내에 안전한 임시 파일 생성
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            for item in items:
                # 딕셔너리를 JSON 문자열로 직렬화하여 줄 단위 기록
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        # OS 수준의 원자적 파일 교체 (중단 없는 안전성 보장)
        os.replace(temp_path, path)
        
    def get_transactions(self) -> Generator[Transaction, None, None]:
        """저장된 거래 내역을 Transaction 객체 스트림으로 반환"""
        for data in self._read_jsonl(self.transactions_path):
            yield Transaction(**data)
            
    def save_transactions(self, transactions: List[Transaction]):
        """전체 거래 목록을 JSONL 파일에 원자적으로 저장"""
        self._write_jsonl_atomic(self.transactions_path, [t.__dict__ for t in transactions])
        
    def get_categories(self) -> Generator[Category, None, None]:
        """저장된 카테고리를 Category 객체 스트림으로 반환"""
        for data in self._read_jsonl(self.categories_path):
            yield Category(**data)
            
    def save_categories(self, categories: List[Category]):
        """카테고리 목록을 JSONL 파일에 원자적으로 저장"""
        self._write_jsonl_atomic(self.categories_path, [c.__dict__ for c in categories])
        
    def get_budgets(self) -> Generator[Budget, None, None]:
        """저장된 예산 데이터를 Budget 객체 스트림으로 반환"""
        for data in self._read_jsonl(self.budgets_path):
            yield Budget(**data)
            
    def save_budgets(self, budgets: List[Budget]):
        """예산 목록을 JSONL 파일에 원자적으로 저장"""
        self._write_jsonl_atomic(self.budgets_path, [b.__dict__ for b in budgets])
