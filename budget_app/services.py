from typing import List, Generator, Optional, Dict, Any
from budget_app.models import Category, Transaction, Budget
from budget_app.repository import Repository
from budget_app.exceptions import ValidationError, NotFoundError
from budget_app.decorators import measure_execution_time, log_action

class BudgetService:
    def __init__(self, repository: Repository):
        self.repo = repository

    @measure_execution_time
    @log_action
    def add_category(self, name: str) -> None:
        categories = list(self.repo.get_categories())
        if any(c.name == name for c in categories):
            raise ValidationError("이미 존재하는 카테고리입니다.", "다른 이름으로 추가해주세요.")
        categories.append(Category(name=name))
        self.repo.save_categories(categories)

    def list_categories(self) -> List[Category]:
        return list(self.repo.get_categories())

    @measure_execution_time
    @log_action
    def remove_category(self, name: str) -> None:
        categories = list(self.repo.get_categories())
        target = next((c for c in categories if c.name == name), None)
        if not target:
            raise NotFoundError(f"'{name}' 카테고리를 찾을 수 없습니다.", "정확한 카테고리 이름을 입력해주세요.")
        if target.is_default:
            raise ValidationError(f"기본 카테고리 '{name}'는 삭제할 수 없습니다.", "추가한 카테고리만 삭제 가능합니다.")
        
        for tx in self.repo.get_transactions():
            if tx.category == name:
                raise ValidationError(f"'{name}' 카테고리에 속한 거래 내역이 있습니다.", "해당 카테고리의 거래 내역을 삭제하거나 수정한 후 다시 시도해주세요.")
                
        categories = [c for c in categories if c.name != name]
        self.repo.save_categories(categories)

    def _validate_date(self, date_str: str) -> None:
        import datetime
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("잘못된 날짜 형식입니다.", "YYYY-MM-DD 형식으로 입력해주세요.")

    def _validate_type(self, type_str: str) -> None:
        if type_str not in ("수입", "지출"):
            raise ValidationError("잘못된 거래 유형입니다.", "'수입' 또는 '지출' 중 하나를 입력해주세요.")

    def _validate_amount(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError("금액은 0보다 커야 합니다.", "양수로 입력해주세요.")

    def _validate_category(self, category_str: str) -> None:
        categories = [c.name for c in self.repo.get_categories()]
        if category_str not in categories:
            raise ValidationError(f"알 수 없는 카테고리입니다: {category_str}", "존재하는 카테고리를 입력해주세요.")

    @measure_execution_time
    @log_action
    def add_transaction(self, date: str, type: str, category: str, amount: int, memo: str, tags: List[str]) -> Transaction:
        self._validate_date(date)
        self._validate_type(type)
        self._validate_category(category)
        self._validate_amount(amount)

        tx = Transaction(date=date, type=type, category=category, amount=amount, memo=memo, tags=tags)
        transactions = list(self.repo.get_transactions())
        transactions.append(tx)
        self.repo.save_transactions(transactions)
        return tx

    def list_transactions(self, limit: Optional[int] = None) -> Generator[Transaction, None, None]:
        transactions = sorted(list(self.repo.get_transactions()), key=lambda x: x.date, reverse=True)
        for i, tx in enumerate(transactions):
            if limit is not None and i >= limit:
                break
            yield tx

