import os
import json
import tempfile
from typing import Generator, List, Any, Dict
from budget_app.models import Transaction, Category, Budget

DEFAULT_CATEGORIES = [
    "food", "transport", "living", "salary", "entertainment", "shopping", "medical", "etc"
]

class Repository:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.transactions_path = os.path.join(data_dir, "transactions.jsonl")
        self.categories_path = os.path.join(data_dir, "categories.jsonl")
        self.budgets_path = os.path.join(data_dir, "budgets.jsonl")
        
        self._init_dir()
        self._init_categories()
        
    def _init_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def _init_categories(self):
        if not os.path.exists(self.categories_path):
            self.save_categories([Category(name=c, is_default=True) for c in DEFAULT_CATEGORIES])

    def _read_jsonl(self, path: str) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def _write_jsonl_atomic(self, path: str, items: List[Dict[str, Any]]):
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        os.replace(temp_path, path)
        
    def get_transactions(self) -> Generator[Transaction, None, None]:
        for data in self._read_jsonl(self.transactions_path):
            yield Transaction(**data)
            
    def save_transactions(self, transactions: List[Transaction]):
        self._write_jsonl_atomic(self.transactions_path, [t.__dict__ for t in transactions])
        
    def get_categories(self) -> Generator[Category, None, None]:
        for data in self._read_jsonl(self.categories_path):
            yield Category(**data)
            
    def save_categories(self, categories: List[Category]):
        self._write_jsonl_atomic(self.categories_path, [c.__dict__ for c in categories])
        
    def get_budgets(self) -> Generator[Budget, None, None]:
        for data in self._read_jsonl(self.budgets_path):
            yield Budget(**data)
            
    def save_budgets(self, budgets: List[Budget]):
        self._write_jsonl_atomic(self.budgets_path, [b.__dict__ for b in budgets])
