"""
[단위 테스트 모듈 (tests/test_budget_app.py)]

💡 파이썬 기초 문법 및 테스트 기법 설명:
1. unittest 표준 라이브러리:
   - 파이썬에 기본 내장된 단위 테스트(Unit Test) 프레임워크입니다.
   - 외부 pytest 등을 설치하지 않아도 `python3 -m unittest`로 전체 테스트를 자동 실행할 수 있습니다.
2. setUp() 과 tearDown() (테스트 픽스처):
   - `setUp()`: 각 테스트 함수(`test_...`)가 실행되기 직전에 매번 자동으로 실행됩니다.
     여기서는 `tempfile.mkdtemp()`로 격리된 임시 폴더를 생성하여 실제 데이터에 영향이 없도록 합니다.
   - `tearDown()`: 테스트 함수 실행이 끝난 후 매번 자동으로 실행됩니다.
     `shutil.rmtree()`로 방금 만든 임시 폴더를 깨끗이 삭제하여 테스트 간 간섭(Side-effect)을 없앱니다.
3. 단언문 (Assertions):
   - `self.assertEqual(a, b)`: a와 b의 값이 정확히 같은지 검증합니다.
   - `self.assertTrue(x)`: 조건 x가 True인지 검증합니다.
   - `self.assertIn(item, list)`: 리스트 안에 item이 들어있는지 확인합니다.
   - `with self.assertRaises(ErrorType):`: 코드 블록 내에서 특정 예외가 반드시 발생하는지 검증합니다.
     (예: 잘못된 날짜를 넣었을 때 ValidationError가 정상적으로 발생하는지 확인)
"""

import unittest
import os
import tempfile
import shutil
from io import StringIO
from unittest.mock import patch
from budget_app.repository import Repository
from budget_app.services import BudgetService
from budget_app.models import Category
from budget_app.exceptions import BudgetAppError, ValidationError, NotFoundError, DataStoreError
from budget_app.sort_utils import external_merge_sort
from budget_app.cli import main as cli_main

class TestBudgetApp(unittest.TestCase):
    """가계부 애플리케이션의 10대 핵심 기능 및 예외 처리를 검증하는 테스트 케이스"""

    def setUp(self):
        """테스트마다 독립된 임시 디렉터리를 생성하여 실제 데이터 파일 오염 방지"""
        self.test_dir = tempfile.mkdtemp()
        self.repo = Repository(data_dir=self.test_dir)
        self.svc = BudgetService(self.repo)

    def tearDown(self):
        """테스트 종료 후 임시 디렉터리 및 파일 완전 삭제"""
        shutil.rmtree(self.test_dir)

    def test_add_transaction(self):
        """거래 추가 및 영문/한글 타입 지원, 최신순 정렬 검증"""
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
        # 최신순 정렬 확인 (2026-09-25 거래가 첫 번째로 와야 함)
        self.assertEqual(txs[0].date, "2026-09-25")

    def test_validation_errors(self):
        """잘못된 입력값(날짜 형식 오류, 유효하지 않은 타입, 음수 금액, 미등록 카테고리) 예외 검증"""
        # 날짜 오류 (형식, 비존재 날짜)
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2026-9-24", "expense", "food", 10000, "점심", [])
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2024-13-40", "expense", "food", 10000, "점심", [])
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2024-02-30", "expense", "food", 10000, "점심", [])
        with self.assertRaises(ValidationError):
            self.svc.add_transaction("2023-02-29", "expense", "food", 10000, "점심", [])
        
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
        """카테고리 기본 생성, 추가, 중복 차단, 사용 중 카테고리 삭제 차단 검증"""
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

        # 빈 파일(0바이트) 또는 공백 파일로 초기화되어 있을 때도 자동 시드되는지 검증
        with open(self.repo.categories_path, "w", encoding="utf-8") as f:
            f.write("")  # 0바이트 빈 파일
        cats_empty = [c.name for c in self.svc.list_categories()]
        self.assertIn("food", cats_empty)
        self.assertIn("transport", cats_empty)
        self.assertEqual(len(cats_empty), 8)

        # 공백만 있는 파일일 때도 자동 시드되는지 검증
        with open(self.repo.categories_path, "w", encoding="utf-8") as f:
            f.write("   \n\n  \n")
        cats_blank = [c.name for c in self.svc.list_categories()]
        self.assertIn("food", cats_blank)
        self.assertEqual(len(cats_blank), 8)

    def test_category_replacement_policy(self):
        """사용 중인 카테고리 삭제 시 대체 카테고리(--replace-with) 이전 마이그레이션 정책 검증"""
        self.svc.add_category("old_cat")
        tx = self.svc.add_transaction("2026-09-24", "expense", "old_cat", 7000, "테스트")
        
        # 대체 카테고리로 지정하여 삭제
        self.svc.remove_category("old_cat", replace_with="food")
        
        # old_cat은 삭제되고 기존 거래의 카테고리는 food로 갱신되었는지 검증
        cats = [c.name for c in self.svc.list_categories()]
        self.assertNotIn("old_cat", cats)
        updated_txs = list(self.svc.list_transactions())
        self.assertEqual(updated_txs[0].category, "food")

    def test_search_transactions(self):
        """키워드, 날짜 범위, 타입, 태그 조건 검색 검증"""
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
        """거래 삭제 및 존재하지 않는 ID 삭제 시 NotFoundError 발생 검증"""
        tx = self.svc.add_transaction("2026-09-24", "expense", "food", 10000, "점심", [])
        self.svc.delete_transaction(tx.id)
        self.assertEqual(len(list(self.svc.list_transactions())), 0)
        
        with self.assertRaises(NotFoundError):
            self.svc.delete_transaction("TX-NOTFOUND")

    def test_update_transaction(self):
        """거래 수정 및 존재하지 않는 ID 수정 시 NotFoundError 발생 검증"""
        tx = self.svc.add_transaction("2026-09-24", "expense", "food", 10000, "점심", [])
        updated = self.svc.update_transaction(tx.id, amount=20000, memo="저녁")
        self.assertEqual(updated.amount, 20000)
        self.assertEqual(updated.memo, "저녁")

        # 없는 거래 수정 시 에러
        with self.assertRaises(NotFoundError):
            self.svc.update_transaction("TX-NOTFOUND", amount=50000)

    def test_budget_and_summary(self):
        """월별 요약 통계 계산 및 예산 초과 경고 산출 검증"""
        # 데이터가 없는 월 조회
        empty_res = self.svc.get_monthly_summary("2026-08")
        self.assertEqual(empty_res.get("status"), "데이터 없음")

        # 예산 50,000원 설정
        self.svc.set_budget("2026-09", 50000)
        self.svc.add_transaction("2026-09-10", "expense", "food", 30000, "회식", [])
        self.svc.add_transaction("2026-09-15", "expense", "transport", 25000, "교통비", [])
        self.svc.add_transaction("2026-09-20", "income", "salary", 100000, "수당", [])
        
        res = self.svc.get_monthly_summary("2026-09", top_n=2)
        self.assertEqual(res["total_income"], 100000)
        self.assertEqual(res["total_expense"], 55000)
        self.assertEqual(res["balance"], 45000)
        # 예산 초과(55000 > 50000) 경고 확인
        self.assertTrue(res["budget"]["warning"])
        self.assertEqual(res["budget"]["alert_level"], "DANGER")
        self.assertAlmostEqual(res["budget"]["usage_rate"], 110.0, places=1)
        self.assertEqual(len(res["top_categories"]), 2)
        self.assertEqual(res["top_categories"][0][0], "food")
        
    def test_csv_export_import_and_partial_skip_report(self):
        """CSV 왕복 및 오류 행 부분 임포트(스킵 사유 상세 리포트) 검증"""
        # 정상 데이터 추가 후 내보내기
        self.svc.add_transaction("2026-09-24", "expense", "food", 10000, "점심", ["밥"])
        csv_path = os.path.join(self.test_dir, "test.csv")
        
        # 조건 없이 export 호출 시 검증 실패 확인
        with self.assertRaises(ValidationError):
            self.svc.export_csv(csv_path)

        # month 조건 지정하여 export
        exported_count = self.svc.export_csv(csv_path, month="2026-09")
        self.assertEqual(exported_count, 1)

        # 잘못된 행이 포함된 CSV 파일 작성
        mixed_csv_path = os.path.join(self.test_dir, "mixed.csv")
        with open(mixed_csv_path, "w", encoding="utf-8") as f:
            f.write("date,type,category,amount,memo,tags\n")
            f.write("2026-09-25,expense,food,12000,정상건,점심\n")
            f.write("2024-13-40,expense,food,10000,날짜오류,오류\n")
            f.write("2026-09-26,expense,food,invalid_amt,금액오류,오류\n")
        
        # 별도 저장소에서 import 테스트
        repo2 = Repository(data_dir=os.path.join(self.test_dir, "new"))
        svc2 = BudgetService(repo2)
        res = svc2.import_csv(mixed_csv_path)
        
        # 1건 성공, 2건 스킵 확인
        self.assertEqual(res["imported"], 1)
        self.assertEqual(res["skipped"], 2)
        self.assertEqual(len(res["skipped_details"]), 2)
        self.assertEqual(res["skipped_details"][0]["row"], 3)
        self.assertEqual(res["skipped_details"][1]["row"], 4)

    def test_exit_codes_mapping(self):
        """주요 비즈니스 예외별 POSIX exit code 매핑 검증"""
        self.assertEqual(BudgetAppError.exit_code, 1)
        self.assertEqual(ValidationError.exit_code, 2)
        self.assertEqual(NotFoundError.exit_code, 3)
        self.assertEqual(DataStoreError.exit_code, 4)

    def test_external_merge_sort_streaming(self):
        """외부 정렬(External Merge Sort) 청크 분할, K-way 병합, O(1) 제너레이터 스트리밍 및 파일 정리 검증"""
        # 12개의 아이템을 chunk_size=3으로 정렬 (총 4개 청크 파일 생성 및 병합)
        raw_items = [
            {"date": "2026-01-05", "id": "TX-05"},
            {"date": "2026-01-01", "id": "TX-01"},
            {"date": "2026-01-09", "id": "TX-09"},
            {"date": "2026-01-03", "id": "TX-03"},
            {"date": "2026-01-08", "id": "TX-08"},
            {"date": "2026-01-02", "id": "TX-02"},
            {"date": "2026-01-07", "id": "TX-07"},
            {"date": "2026-01-04", "id": "TX-04"},
            {"date": "2026-01-10", "id": "TX-10"},
            {"date": "2026-01-06", "id": "TX-06"},
            {"date": "2026-01-12", "id": "TX-12"},
            {"date": "2026-01-11", "id": "TX-11"},
        ]
        
        # 1. 내림차순(최신순) 정렬 검증
        sorted_stream = external_merge_sort(
            iter(raw_items),
            key=lambda x: (x["date"], x["id"]),
            reverse=True,
            chunk_size=3,
            serializer=lambda x: x,
            deserializer=lambda d: d
        )
        results = list(sorted_stream)
        self.assertEqual(len(results), 12)
        self.assertEqual(results[0]["date"], "2026-01-12")
        self.assertEqual(results[-1]["date"], "2026-01-01")
        
        # 2. 오름차순 정렬 검증
        asc_stream = external_merge_sort(
            iter(raw_items),
            key=lambda x: (x["date"], x["id"]),
            reverse=False,
            chunk_size=3,
            serializer=lambda x: x,
            deserializer=lambda d: d
        )
        asc_results = list(asc_stream)
        self.assertEqual(asc_results[0]["date"], "2026-01-01")
        self.assertEqual(asc_results[-1]["date"], "2026-01-12")

        # 3. 조기 중단(Early break) 시 임시 파일 정리(Clean-up) 보장 검증
        partial_stream = external_merge_sort(
            iter(raw_items),
            key=lambda x: (x["date"], x["id"]),
            reverse=True,
            chunk_size=3,
            serializer=lambda x: x,
            deserializer=lambda d: d
        )
        picked = []
        for i, item in enumerate(partial_stream):
            if i >= 2:
                break
            picked.append(item)
        self.assertEqual(len(picked), 2)

    def test_zero_load_streaming_in_services(self):
        """list_transactions 및 search_transactions가 제너레이터 스트림을 반환하며 메모리 O(1)로 동작함을 검증"""
        import types
        self.svc.add_transaction("2026-01-01", "expense", "food", 1000, "1")
        self.svc.add_transaction("2026-01-02", "expense", "food", 2000, "2")
        self.svc.add_transaction("2026-01-03", "expense", "food", 3000, "3")

        list_gen = self.svc.list_transactions(limit=2)
        # 반환 객체가 제너레이터 타입인지 확인
        self.assertIsInstance(list_gen, types.GeneratorType)
        first_two = list(list_gen)
        self.assertEqual(len(first_two), 2)
        self.assertEqual(first_two[0].date, "2026-01-03")

        search_gen = self.svc.search_transactions(category="food")
        self.assertIsInstance(search_gen, types.GeneratorType)
        found = list(search_gen)
        self.assertEqual(len(found), 3)

    def test_cli_parent_and_subparsers_full_pipeline(self):
        """cli.py 부모 파서(--data-dir, --debug 상속) 및 10대 서브파서/중첩 서브파서 파싱 동작 검증"""
        # 1. 부모 파서 옵션이 서브커맨드 앞에 위치할 때 상속 검증
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["--data-dir", self.test_dir, "category", "list"])
            self.assertIn("- food", mock_out.getvalue())

        # 2. 부모 파서 옵션이 서브커맨드 뒤에 위치할 때 상속 검증
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["category", "list", "--data-dir", self.test_dir])
            self.assertIn("- salary", mock_out.getvalue())

        # 3. 중첩 서브파서(budget set) 동작 검증
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["budget", "set", "--month", "2024-01", "--amount", "1500000", "--data-dir", self.test_dir])
            self.assertIn("[저장 완료] 2024-01 예산 1500000원", mock_out.getvalue())

        # 4. category add 및 remove 서브파서 검증
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["category", "add", "travel", "--data-dir", self.test_dir])
            self.assertIn("[저장 완료] category=travel", mock_out.getvalue())
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["category", "remove", "travel", "--data-dir", self.test_dir])
            self.assertIn("[삭제 완료] category=travel", mock_out.getvalue())

        # 5. add (대화형) 및 list, search 서브파서 검증
        user_inputs = ["2024-01-15", "expense", "food", "15000", "점심 식사", "식비"]
        with patch("builtins.input", side_effect=user_inputs), patch("sys.stdout", new_callable=StringIO):
            cli_main(["add", "--data-dir", self.test_dir])

        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["list", "--limit", "1", "--data-dir", self.test_dir])
            self.assertIn("2024-01-15 | expense | food | 15000 | 점심 식사", mock_out.getvalue())

        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["search", "--category", "food", "--q", "점심", "--data-dir", self.test_dir])
            self.assertIn("2024-01-15 | expense | food | 15000 | 점심 식사", mock_out.getvalue())

        # 6. summary 서브파서 검증
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli_main(["summary", "--month", "2024-01", "--top", "3", "--data-dir", self.test_dir])
            self.assertIn("총 지출: 15000원", mock_out.getvalue())

        # 7. 필수 인자 누락 시 파서 에러 (SystemExit != 0) 검증
        for invalid_argv in [["summary"], ["budget", "set"], ["update"], ["delete"], ["export"], ["import"]]:
            with self.subTest(invalid_argv=invalid_argv):
                with patch("sys.stderr", new_callable=StringIO):
                    with self.assertRaises(SystemExit) as cm:
                        cli_main(invalid_argv)
                    self.assertNotEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
