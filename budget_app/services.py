"""
[비즈니스 로직 및 서비스 모듈 (services.py)]

💡 파이썬 기초 문법 및 비즈니스 설계 설명:
1. 서비스 레이어 (Service Layer)의 역할:
   - 사용자의 입력 방식(CLI, 대화형 콘솔 등)이나 저장 방식(JSONL, CSV 등)과 무관하게,
     "비즈니스 규칙 검증(날짜, 금액, 카테고리 체크)"과 "핵심 계산(수입/지출 합산, 예산 사용률, TOP N 집계)"을 담당합니다.
2. 정규 표현식 (Regular Expression - re 모듈):
   - `re.match(r"^\d{4}-\d{2}-\d{2}$", date_str)`: 
     * `^`와 `$`: 문자열의 시작과 끝을 의미
     * `\d{4}`: 숫자 4자리(년도), `\d{2}`: 숫자 2자리(월, 일)
     * 형식이 일치하지 않으면 None을 반환하므로 빠르게 포맷을 검사할 수 있습니다.
3. 날짜 검증 (datetime.strptime):
   - 2024-13-40 처럼 정규식 포맷은 맞아도 실제 달력에 존재하지 않는 가짜 날짜는
     `datetime.datetime.strptime(date_str, "%Y-%m-%d")`가 `ValueError`를 발생시켜 정밀하게 판별합니다.
4. collections.defaultdict:
   - 일반 딕셔너리는 존재하지 않는 키에 `d["food"] += 1000`을 시도하면 `KeyError`가 납니다.
   - `defaultdict(int)`는 새로운 키가 들어올 때 자동으로 초기값 `0`을 세팅해주어 카테고리별 누적 합계를 매우 깔끔하게 작성할 수 있습니다.
5. sorted() 함수와 람다 키(key):
   - `sorted(items, key=lambda x: x[1], reverse=True)`: 
     각 항목의 1번째 원소(금액)를 기준으로 내림차순(`reverse=True`) 정렬하여 상위(TOP) 카테고리를 추출합니다.
6. 표준 csv 모듈 (csv.writer, csv.DictReader):
   - 외부 무거운 라이브러리(pandas 등) 없이 파이썬 표준 라이브러리만으로 CSV 헤더 작성과 딕셔너리 기반 행 파싱을 안전하게 수행합니다.
"""

import csv
import datetime
import os
import re
from collections import defaultdict
from typing import List, Generator, Optional, Dict, Any

from budget_app.models import Category, Transaction, Budget
from budget_app.repository import Repository
from budget_app.exceptions import ValidationError, NotFoundError
from budget_app.decorators import measure_execution_time, log_action

class BudgetService:
    """
    가계부의 10대 핵심 비즈니스 로직(거래 추가, 조회, 검색, 수정, 삭제, 요약, 예산, 카테고리, CSV)을 총괄하는 서비스 클래스
    """
    def __init__(self, repository: Repository):
        self.repo = repository

    @measure_execution_time
    @log_action
    def add_category(self, name: str) -> None:
        """신규 카테고리 추가 (중복 검사 포함)"""
        name = name.strip()
        if not name:
            raise ValidationError("카테고리 이름이 비어 있습니다.", "카테고리 이름을 입력해주세요 (예: food).")
        categories = list(self.repo.get_categories())
        # 동일한 이름의 카테고리가 이미 존재하는지 확인
        if any(c.name == name for c in categories):
            raise ValidationError(f"이미 존재하는 카테고리입니다: '{name}'", "다른 이름으로 추가해주세요.")
        categories.append(Category(name=name))
        self.repo.save_categories(categories)

    def list_categories(self) -> List[Category]:
        """등록된 전체 카테고리 목록 반환"""
        return list(self.repo.get_categories())

    @measure_execution_time
    @log_action
    def remove_category(self, name: str) -> None:
        """
        카테고리 삭제:
        1. 기본 카테고리는 삭제 불가
        2. 거래 내역에서 사용 중인 카테고리는 데이터 보호를 위해 삭제 차단
        """
        name = name.strip()
        categories = list(self.repo.get_categories())
        target = next((c for c in categories if c.name == name), None)
        if not target:
            raise NotFoundError(f"'{name}' 카테고리를 찾을 수 없습니다.", "category list 명령어로 등록된 카테고리를 확인하세요.")
        if target.is_default:
            raise ValidationError(f"기본 카테고리 '{name}'는 삭제할 수 없습니다.", "사용자가 직접 추가한 카테고리만 삭제 가능합니다.")
        
        # 참조 무결성 검사: 삭제 대상 카테고리를 참조하는 거래가 있는지 확인
        for tx in self.repo.get_transactions():
            if tx.category == name:
                raise ValidationError(
                    f"'{name}' 카테고리를 사용하는 거래 내역이 존재합니다.",
                    "해당 카테고리의 거래 내역을 삭제하거나 수정한 후 다시 시도하세요."
                )
                
        categories = [c for c in categories if c.name != name]
        self.repo.save_categories(categories)

    def _validate_date(self, date_str: str) -> None:
        """날짜 형식(YYYY-MM-DD) 및 달력상 실제 유효 날짜 검증"""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise ValidationError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2024-01-15")
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2024-01-15")

    def _validate_type(self, type_str: str) -> str:
        """거래 유형(수입/지출 또는 income/expense) 검증 및 영문 표준화"""
        norm = type_str.strip().lower()
        if norm in ("income", "수입"):
            return "income"
        elif norm in ("expense", "지출"):
            return "expense"
        raise ValidationError("허용되지 않은 type입니다.", "타입은 'income' 또는 'expense'로 입력해주세요 (수입/지출도 허용).")

    def _validate_amount(self, amount: int) -> None:
        """금액의 양수 조건 검증"""
        if amount <= 0:
            raise ValidationError("금액은 0보다 큰 양수여야 합니다.", "1 이상의 양의 정수로 입력해주세요.")

    def _validate_category(self, category_str: str) -> None:
        """입력한 카테고리가 등록된 카테고리인지 검증"""
        categories = [c.name for c in self.repo.get_categories()]
        if category_str not in categories:
            raise ValidationError(
                f"존재하지 않는 category입니다: '{category_str}'",
                f"등록된 카테고리 목록: {', '.join(categories)} (category add로 추가 가능)"
            )

    @measure_execution_time
    @log_action
    def add_transaction(self, date: str, type: str, category: str, amount: int, memo: str = "", tags: Optional[List[str]] = None) -> Transaction:
        """새로운 거래 내역을 유효성 검증 후 추가하고 영구 저장"""
        self._validate_date(date)
        validated_type = self._validate_type(type)
        self._validate_category(category)
        self._validate_amount(amount)
        if tags is None:
            tags = []

        tx = Transaction(date=date, type=validated_type, category=category, amount=amount, memo=memo, tags=tags)
        transactions = list(self.repo.get_transactions())
        transactions.append(tx)
        self.repo.save_transactions(transactions)
        return tx

    def list_transactions(self, limit: Optional[int] = None) -> Generator[Transaction, None, None]:
        """
        거래 목록을 최신순(날짜 내림차순)으로 정렬하여,
        요청 개수(limit)만큼 한 건씩 스트리밍(yield)으로 반환
        """
        transactions = sorted(list(self.repo.get_transactions()), key=lambda x: (x.date, x.id), reverse=True)
        for i, tx in enumerate(transactions):
            if limit is not None and i >= limit:
                break
            yield tx

    def search_transactions(self, from_date: Optional[str] = None, to_date: Optional[str] = None, 
                            category: Optional[str] = None, type: Optional[str] = None, 
                            q: Optional[str] = None, tag: Optional[str] = None) -> Generator[Transaction, None, None]:
        """
        다중 조건(기간, 카테고리, 유형, 메모 검색어, 태그)을 만족하는 거래를 필터링하여 최신순 스트리밍 반환
        """
        if from_date: self._validate_date(from_date)
        if to_date: self._validate_date(to_date)
        
        normalized_type = None
        if type:
            normalized_type = self._validate_type(type)
            
        transactions = sorted(list(self.repo.get_transactions()), key=lambda x: (x.date, x.id), reverse=True)
        for tx in transactions:
            if from_date and tx.date < from_date: continue
            if to_date and tx.date > to_date: continue
            if category and tx.category.lower() != category.lower(): continue
            if normalized_type and tx.type != normalized_type: continue
            if q and q.lower() not in tx.memo.lower(): continue
            if tag and tag not in tx.tags: continue
            yield tx
            
    @measure_execution_time
    @log_action
    def update_transaction(self, id: str, date: Optional[str] = None, type: Optional[str] = None, 
                           category: Optional[str] = None, amount: Optional[int] = None, 
                           memo: Optional[str] = None, tags: Optional[List[str]] = None) -> Transaction:
        """기존 거래 내역의 특정 필드만 선택적으로 수정"""
        transactions = list(self.repo.get_transactions())
        target = next((tx for tx in transactions if tx.id == id), None)
        if not target:
            raise NotFoundError(f"ID '{id}'에 해당하는 거래를 찾을 수 없습니다.", "list 명령어로 올바른 거래 ID를 확인하세요.")
            
        if date: 
            self._validate_date(date)
            target.date = date
        if type: 
            target.type = self._validate_type(type)
        if category: 
            self._validate_category(category)
            target.category = category
        if amount is not None: 
            self._validate_amount(amount)
            target.amount = amount
        if memo is not None: target.memo = memo
        if tags is not None: target.tags = tags
            
        self.repo.save_transactions(transactions)
        return target
        
    @measure_execution_time
    @log_action
    def delete_transaction(self, id: str) -> None:
        """거래 ID 기반 특정 거래 삭제"""
        transactions = list(self.repo.get_transactions())
        initial_len = len(transactions)
        transactions = [tx for tx in transactions if tx.id != id]
        if len(transactions) == initial_len:
            raise NotFoundError(f"ID '{id}'에 해당하는 거래를 찾을 수 없습니다.", "list 명령어로 올바른 거래 ID를 확인하세요.")
        self.repo.save_transactions(transactions)

    @measure_execution_time
    @log_action
    def set_budget(self, month: str, amount: int) -> Budget:
        """특정 월의 목표 예산 금액 설정 및 영구 저장"""
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationError("잘못된 월 형식입니다 (YYYY-MM).", "예: 2024-01")
        if amount <= 0:
            raise ValidationError("예산 금액은 0보다 큰 양수여야 합니다.", "1 이상의 양의 정수로 입력해주세요.")
            
        budgets = list(self.repo.get_budgets())
        target = next((b for b in budgets if b.month == month), None)
        if target:
            target.amount = amount
        else:
            target = Budget(month=month, amount=amount)
            budgets.append(target)
        self.repo.save_budgets(budgets)
        return target

    def get_budget(self, month: str) -> Optional[Budget]:
        """해당 월에 설정된 예산 조회"""
        return next((b for b in self.repo.get_budgets() if b.month == month), None)

    @measure_execution_time
    def get_monthly_summary(self, month: str, top_n: int = 3) -> Dict[str, Any]:
        """
        월별 재정 요약 통계 계산:
        - 총 수입, 총 지출, 잔액 계산
        - 카테고리별 지출 상위 TOP N 집계
        - 설정된 예산이 있는 경우 사용률(%) 및 예산 초과 경고 산출
        """
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationError("잘못된 월 형식입니다 (YYYY-MM).", "예: 2024-01")
            
        total_income = 0
        total_expense = 0
        category_expenses = defaultdict(int)
        
        has_data = False
        for tx in self.repo.get_transactions():
            if tx.date.startswith(month):
                has_data = True
                if tx.type in ("수입", "income"):
                    total_income += tx.amount
                elif tx.type in ("지출", "expense"):
                    total_expense += tx.amount
                    category_expenses[tx.category] += tx.amount
                    
        # 해당 월에 데이터가 전혀 없으면 상태 반환
        if not has_data:
            return {"status": "데이터 없음"}
            
        balance = total_income - total_expense
        # 지출 금액이 큰 순서대로 상위 N개 카테고리 추출
        top_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # 예산 비교 분석
        budget = self.get_budget(month)
        budget_info = None
        if budget:
            usage_rate = (total_expense / budget.amount) * 100 if budget.amount > 0 else 0
            warning = usage_rate > 100
            budget_info = {
                "amount": budget.amount,
                "usage_rate": usage_rate,
                "warning": warning
            }
            
        return {
            "status": "success",
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "top_categories": top_categories,
            "budget": budget_info
        }

    @measure_execution_time
    @log_action
    def export_csv(self, path: str, month: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> int:
        """
        조건(특정 월 또는 기간 범위)에 일치하는 거래 내역을 규격화된 CSV 포맷으로 파일 출력
        (컬럼 순서: date, type, category, amount, memo, tags)
        """
        if not month and not (from_date and to_date):
            raise ValidationError(
                "export 조건이 누락되었습니다.",
                "--month YYYY-MM 또는 --from YYYY-MM-DD --to YYYY-MM-DD 중 하나 이상의 조건을 지정하세요."
            )
        if month:
            if not re.match(r"^\d{4}-\d{2}$", month):
                raise ValidationError("잘못된 월 형식입니다 (YYYY-MM).", "예: 2024-01")
        if from_date: self._validate_date(from_date)
        if to_date: self._validate_date(to_date)

        count = 0
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])
            for tx in self.search_transactions(from_date=from_date, to_date=to_date):
                if month and not tx.date.startswith(month):
                    continue
                tags_str = ",".join(tx.tags)
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, tags_str])
                count += 1
        return count

    @measure_execution_time
    @log_action
    def import_csv(self, path: str) -> Dict[str, int]:
        """
        외부 CSV 파일로부터 거래 내역을 한 줄씩 읽어 일괄 등록.
        형식 오류 행은 건너뛰고(skip) 성공 건수와 실패 건수를 집계하여 반환
        """
        if not os.path.exists(path):
            raise NotFoundError(f"파일을 찾을 수 없습니다: {path}", "가져올 CSV 파일의 경로를 다시 확인해주세요.")
            
        imported = 0
        skipped = 0
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = (row.get('date') or '').strip()
                    type_str = (row.get('type') or '').strip()
                    category = (row.get('category') or '').strip()
                    amount_val = int((row.get('amount') or '0').strip())
                    memo = (row.get('memo') or '').strip()
                    tags_str = (row.get('tags') or '').strip()
                    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
                    
                    self.add_transaction(date, type_str, category, amount_val, memo, tags)
                    imported += 1
                except Exception:
                    skipped += 1
                    
        return {"imported": imported, "skipped": skipped}
