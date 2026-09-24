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
        # 영문 type 지원 (expense / income)
        tx = self.svc.add_transaction("2026-09-24", "expense", "food", 15000, "점심", ["밥", "외식"])
        self.assertEqual(tx.amount, 15000)
        self.assertEqual(tx.type, "expense")
        self.assertTrue(tx.id.startswith("TX-"))

        # 한글 type 지원 (지출 / 수입)
        tx2 = self.svc.add_transaction("2026-09-25", "수입", "salary", 3000000, "월급", [])
        self.assertEqual(tx2.type, "income")
        
        txs = list(self.svc.list_transactions())
        self.assertEqual(len(txs), 2)
        # 최신순 정렬 확인 (2026-09-25가 첫 번째)
        self.assertEqual(txs[0].date, "2026-09-25")

    def test_validation_errors(self):
        # 날짜 오류 (형식, 비존재 날짜)
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-9-24", "expense", "food", 10000, "점심", [])
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2024-13-40", "expense", "food", 10000, "점심", [])
        
        # 타입 오류
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "invalid_type", "food", 10000, "점심", [])
            
        # 금액 음수/0 오류
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "expense", "food", -500, "점심", [])
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "expense", "food", 0, "점심", [])
            
        # 미등록 카테고리 오류
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-09-24", "expense", "nonexistent", 10000, "점심", [])

    def test_category_management(self):
        # 기본 카테고리 자동 생성 확인
        cats = [c.name for c in self.svc.list_categories()]
        self.assertIn("food", cats)
        self.assertIn("transport", cats)
        
        # 카테고리 추가
        self.svc.add_category("custom_hobby")
        cats = [c.name for c in self.svc.list_categories()]
        self.assertIn("custom_hobby", cats)
        
        # 중복 추가 오류
        with self.assertRaises(ValidationError):
            self.svc.add_category("custom_hobby")
            
        # 기본 카테고리 삭제 차단
        with self.assertRaises(ValidationError):
            self.svc.remove_category("food")
            
        # 사용 중인 카테고리 삭제 차단
        self.svc.add_transaction("2026-09-24", "expense", "custom_hobby", 5000)
        with self.assertRaises(ValidationError):
            self.svc.remove_category("custom_hobby")
            
        # 거래 삭제 후 카테고리 삭제 성공
        tx = list(self.svc.list_transactions())[0]
        self.svc.delete_transaction(tx.id)
        self.svc.remove_category("custom_hobby")
        self.assertNotIn("custom_hobby", [c.name for c in self.svc.list_categories()])

    def test_search_transactions(self):
        self.svc.add_transaction("2026-01-10", "expense", "food", 10000, "돈까스", ["점심"])
        self.svc.add_transaction("2026-01-20", "expense", "transport", 2000, "버스", ["대중교통"])
        self.svc.add_transaction("2026-02-05", "income", "salary", 500000, "알바비", ["부수입"])

        # 키워드 검색
        res_q = list(self.svc.search_transactions(q="돈까스"))
        self.assertEqual(len(res_q), 1)
        self.assertEqual(res_q[0].memo, "돈까스")

        # 날짜 범위 검색
        res_date = list(self.svc.search_transactions(from_date="2026-01-01", to_date="2026-01-31"))
        self.assertEqual(len(res_date), 2)

        # 타입 검색
        res_type = list(self.svc.search_transactions(type="income"))
        self.assertEqual(len(res_type), 1)

        # 태그 검색
        res_tag = list(self.svc.search_transactions(tag="대중교통"))
        self.assertEqual(len(res_tag), 1)

    def test_delete_transaction(self):
        tx = self.svc.add_transaction("2026-09-24", "expense", "food", 10000, "점심", [])
        self.svc.delete_transaction(tx.id)
        self.assertEqual(len(list(self.svc.list_transactions())), 0)
        
        with self.assertRaises(NotFoundError):
            self.svc.delete_transaction("TX-NOTFOUND")

    def test_update_transaction(self):
        tx = self.svc.add_transaction("2026-09-24", "expense", "food", 10000, "점심", [])
        updated = self.svc.update_transaction(tx.id, amount=20000, memo="저녁")
        self.assertEqual(updated.amount, 20000)
        self.assertEqual(updated.memo, "저녁")

        # 없는 거래 수정 시 에러
        with self.assertRaises(NotFoundError):
            self.svc.update_transaction("TX-NOTFOUND", amount=50000)

    def test_budget_and_summary(self):
        # 빈 데이터 조회
        empty_res = self.svc.get_monthly_summary("2026-08")
        self.assertEqual(empty_res.get("status"), "데이터 없음")

        # 예산 설정
        self.svc.set_budget("2026-09", 50000)
        self.svc.add_transaction("2026-09-10", "expense", "food", 30000, "회식", [])
        self.svc.add_transaction("2026-09-15", "expense", "transport", 25000, "교통비", [])
        self.svc.add_transaction("2026-09-20", "income", "salary", 100000, "수당", [])
        
        res = self.svc.get_monthly_summary("2026-09", top_n=2)
        self.assertEqual(res["total_income"], 100000)
        self.assertEqual(res["total_expense"], 55000)
        self.assertEqual(res["balance"], 45000)
        self.assertTrue(res["budget"]["warning"])
        self.assertAlmostEqual(res["budget"]["usage_rate"], 110.0, places=1)
        self.assertEqual(len(res["top_categories"]), 2)
        self.assertEqual(res["top_categories"][0][0], "food")
        
    def test_csv_export_import(self):
        self.svc.add_transaction("2026-09-24", "expense", "food", 10000, "점심", ["밥"])
        csv_path = os.path.join(self.test_dir, "test.csv")
        
        # 조건 없이 export 호출 시 검증 실패
        with self.assertRaises(ValidationError):
            self.svc.export_csv(csv_path)

        # month 조건 지정하여 export
        exported_count = self.svc.export_csv(csv_path, month="2026-09")
        self.assertEqual(exported_count, 1)
        
        # 별도 저장소에서 import 테스트
        repo2 = Repository(data_dir=os.path.join(self.test_dir, "new"))
        svc2 = BudgetService(repo2)
        res = svc2.import_csv(csv_path)
        
        self.assertEqual(res["imported"], 1)
        self.assertEqual(res["skipped"], 0)
        txs = list(svc2.list_transactions())
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].amount, 10000)
        self.assertEqual(txs[0].memo, "점심")

if __name__ == "__main__":
    unittest.main()
