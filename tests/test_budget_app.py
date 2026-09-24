import unittest
import os
import tempfile
import shutil
from budget_app.repository import Repository
from budget_app.services import BudgetService
from budget_app.models import Category
from budget_app.exceptions import ValidationError, NotFoundError

class TestBudgetApp(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo = Repository(data_dir=self.test_dir)
        self.svc = BudgetService(self.repo)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_transaction(self):
        tx = self.svc.add_transaction("2026-09-24", "지출", "food", 10000, "점심", ["밥", "외식"])
        self.assertEqual(tx.amount, 10000)
        
        txs = list(self.svc.list_transactions())
        self.assertEqual(len(txs), 1)

    def test_validation_errors(self):
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-9-24", "지출", "food", 10000, "점심", [])
        
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "이상한유형", "food", 10000, "점심", [])
            
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "지출", "food", -500, "점심", [])
            
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "지출", "nonexistent", 10000, "점심", [])

    def test_category_management(self):
        self.svc.add_category("mycat")
        cats = [c.name for c in self.svc.list_categories()]
        self.assertIn("mycat", cats)
        
        with self.assertRaises(ValidationError):
            self.svc.add_category("mycat")
            
        self.svc.remove_category("mycat")
        cats = [c.name for c in self.svc.list_categories()]
        self.assertNotIn("mycat", cats)

        with self.assertRaises(ValidationError):
            self.svc.remove_category("food") # default

    def test_delete_transaction(self):
        tx = self.svc.add_transaction("2026-09-24", "지출", "food", 10000, "점심", [])
        self.svc.delete_transaction(tx.id)
        self.assertEqual(len(list(self.svc.list_transactions())), 0)
        
        with self.assertRaises(NotFoundError):
            self.svc.delete_transaction("INVALID-ID")

    def test_update_transaction(self):
        tx = self.svc.add_transaction("2026-09-24", "지출", "food", 10000, "점심", [])
        updated = self.svc.update_transaction(tx.id, amount=20000, memo="저녁")
        self.assertEqual(updated.amount, 20000)
        self.assertEqual(updated.memo, "저녁")

    def test_budget_and_summary(self):
        self.svc.set_budget("2026-09", 50000)
        self.svc.add_transaction("2026-09-10", "지출", "food", 30000, "회식", [])
        self.svc.add_transaction("2026-09-15", "지출", "transport", 25000, "교통비", [])
        
        res = self.svc.get_monthly_summary("2026-09")
        self.assertEqual(res["total_expense"], 55000)
        self.assertTrue(res["budget"]["warning"])
        
    def test_csv_export_import(self):
        self.svc.add_transaction("2026-09-24", "지출", "food", 10000, "점심", ["밥"])
        csv_path = os.path.join(self.test_dir, "test.csv")
        self.svc.export_csv(csv_path)
        
        repo2 = Repository(data_dir=os.path.join(self.test_dir, "new"))
        svc2 = BudgetService(repo2)
        res = svc2.import_csv(csv_path)
        
        self.assertEqual(res["imported"], 1)
        self.assertEqual(len(list(svc2.list_transactions())), 1)

if __name__ == "__main__":
    unittest.main()
