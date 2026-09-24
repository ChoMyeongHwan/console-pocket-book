from dataclasses import dataclass, field
from typing import List
import uuid

@dataclass
class Transaction:
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"TX-{uuid.uuid4().hex[:6].upper()}")

@dataclass
class Category:
    name: str
    is_default: bool = False

@dataclass
class Budget:
    month: str
    amount: int
