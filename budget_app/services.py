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
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise ValidationError("잘못된 날짜 형식입니다.", "YYYY-MM-DD 형식으로 입력해주세요.")
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("존재하지 않는 날짜입니다.", "유효한 날짜를 입력해주세요.")

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

    def search_transactions(self, from_date: Optional[str] = None, to_date: Optional[str] = None, 
                            category: Optional[str] = None, type: Optional[str] = None, 
                            q: Optional[str] = None, tag: Optional[str] = None) -> Generator[Transaction, None, None]:
        if from_date: self._validate_date(from_date)
        if to_date: self._validate_date(to_date)
            
        for tx in self.repo.get_transactions():
            if from_date and tx.date < from_date: continue
            if to_date and tx.date > to_date: continue
            if category and tx.category != category: continue
            if type and tx.type != type: continue
            if q and q.lower() not in tx.memo.lower(): continue
            if tag and tag not in tx.tags: continue
            yield tx
            
    @measure_execution_time
    @log_action
    def update_transaction(self, id: str, date: Optional[str] = None, type: Optional[str] = None, 
                           category: Optional[str] = None, amount: Optional[int] = None, 
                           memo: Optional[str] = None, tags: Optional[List[str]] = None) -> Transaction:
        transactions = list(self.repo.get_transactions())
        target = next((tx for tx in transactions if tx.id == id), None)
        if not target:
            raise NotFoundError("해당 거래를 찾을 수 없습니다.", "정확한 ID를 입력해주세요.")
            
        if date: 
            self._validate_date(date)
            target.date = date
        if type: 
            self._validate_type(type)
            target.type = type
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
        transactions = list(self.repo.get_transactions())
        initial_len = len(transactions)
        transactions = [tx for tx in transactions if tx.id != id]
        if len(transactions) == initial_len:
            raise NotFoundError("해당 거래를 찾을 수 없습니다.", "정확한 ID를 입력해주세요.")
        self.repo.save_transactions(transactions)

    @measure_execution_time
    @log_action
    def set_budget(self, month: str, amount: int) -> Budget:
        import re
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationError("잘못된 월 형식입니다.", "YYYY-MM 형식으로 입력해주세요.")
        if amount <= 0:
            raise ValidationError("예산 금액은 0보다 커야 합니다.", "양수로 입력해주세요.")
            
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
        return next((b for b in self.repo.get_budgets() if b.month == month), None)

    @measure_execution_time
    def get_monthly_summary(self, month: str, top_n: int = 3) -> Dict[str, Any]:
        import re
        from collections import defaultdict
        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValidationError("잘못된 월 형식입니다.", "YYYY-MM 형식으로 입력해주세요.")
            
        total_income = 0
        total_expense = 0
        category_expenses = defaultdict(int)
        
        has_data = False
        for tx in self.repo.get_transactions():
            if tx.date.startswith(month):
                has_data = True
                if tx.type == "수입":
                    total_income += tx.amount
                elif tx.type == "지출":
                    total_expense += tx.amount
                    category_expenses[tx.category] += tx.amount
                    
        if not has_data:
            return {"status": "데이터 없음"}
            
        balance = total_income - total_expense
        top_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
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
    def export_csv(self, path: str, month: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> None:
        import csv
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])
            for tx in self.search_transactions(from_date=from_date, to_date=to_date):
                if month and not tx.date.startswith(month): continue
                tags_str = ",".join(tx.tags)
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, tags_str])

    @measure_execution_time
    @log_action
    def import_csv(self, path: str) -> Dict[str, int]:
        import csv
        import os
        if not os.path.exists(path):
            raise NotFoundError("파일을 찾을 수 없습니다.", "정확한 경로를 입력해주세요.")
            
        imported = 0
        skipped = 0
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = row.get('date', '')
                    type_str = row.get('type', '')
                    category = row.get('category', '')
                    amount = int(row.get('amount', 0))
                    memo = row.get('memo', '')
                    tags_str = row.get('tags', '')
                    tags = [t.strip() for t in tags_str.split(',')] if tags_str else []
                    
                    self.add_transaction(date, type_str, category, amount, memo, tags)
                    imported += 1
                except Exception:
                    skipped += 1
                    
        return {"imported": imported, "skipped": skipped}

