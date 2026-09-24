"""
[CLI 커맨드 라인 인터페이스 모듈 (cli.py)]

💡 파이썬 기초 문법 및 CLI 설계 설명:
1. argparse 표준 라이브러리:
   - 터미널에서 사용자가 입력하는 커맨드 라인 옵션(`--help`, `--limit 5`, `--from 2024-01-01` 등)을 파싱하여
     파이썬 객체(`args.limit`, `args.from_date`)로 변환해주는 파이썬 표준 라이브러리입니다.
2. 서브파서 (Subparsers - add_subparsers):
   - `git commit`, `git push` 처럼 하나의 프로그램 안에서 여러 하위 명령어(`add`, `list`, `summary`, `budget` 등)를
     분기 처리할 수 있게 해주는 구조입니다.
3. 부모 파서 (Parent Parser - parents=[parent_parser]):
   - 모든 하위 명령어에서 공통으로 쓸 옵션(`--data-dir`)을 한 번만 정의해두고,
     각 서브파서가 `parents=[parent_parser]`로 물려받게 함으로써 코드 중복을 제거합니다.
4. 예약어 피하기 (dest="from_date"):
   - 파이썬에서 `from`은 `from module import ...`에 사용되는 '예약어(Keyword)'이므로 변수명으로 쓸 수 없습니다.
   - 따라서 CLI 옵션은 리눅스 표준인 `--from`으로 받되, 파이썬 내부 변수명은 `dest="from_date"`로 안전하게 매핑합니다.
5. 대화형 입력 (input)과 KeyboardInterrupt:
   - `input("메시지: ")`는 사용자가 터미널에서 글자를 치고 엔터를 누를 때까지 대기하며 문자열을 반환합니다.
   - 사용자가 작업 중 `Ctrl + C`를 눌러 취소하면 `KeyboardInterrupt` 예외가 발생하는데, 이를 try-except로 잡아 깔끔하게 종료 안내를 출력합니다.
"""

import argparse
import sys
from budget_app.repository import Repository
from budget_app.services import BudgetService
from budget_app.decorators import handle_cli_error
from budget_app.exceptions import ValidationError

def _print_tx(tx):
    """단일 거래 내역을 규격화된 한 줄 텍스트로 콘솔에 출력 (ID | 날짜 | 타입 | 카테고리 | 금액 | 메모)"""
    memo_str = tx.memo if tx.memo else ""
    print(f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount} | {memo_str}")

@handle_cli_error
def main(argv=None):
    """
    애플리케이션 진입 함수:
    명령줄 인자를 파싱하고 적절한 서비스 메서드를 호출하여 결과를 터미널에 출력합니다.
    """
    # 하위 모든 서브커맨드에서 공유할 부모 파서 정의 (공통 옵션: --data-dir)
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--data-dir", default="./data", help="데이터 저장 디렉터리 (기본값: ./data)")

    # 메인 파서 생성
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="콘솔 용돈 기입장 (가계부) 프로그램",
        parents=[parent_parser]
    )
    
    # 10대 핵심 기능별 서브커맨드 등록
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어")

    # 1. 거래 추가 (add) - 대화형 입력
    subparsers.add_parser("add", help="거래 추가 (대화형 입력)", parents=[parent_parser])

    # 2. 거래 목록 조회 (list)
    parser_list = subparsers.add_parser("list", help="거래 목록 조회 (최신순)", parents=[parent_parser])
    parser_list.add_argument("--limit", type=int, help="출력할 거래 건수")

    # 3. 거래 다중 조건 검색 (search)
    parser_search = subparsers.add_parser("search", help="거래 검색", parents=[parent_parser])
    parser_search.add_argument("--from", dest="from_date", help="검색 시작일 (YYYY-MM-DD)")
    parser_search.add_argument("--to", dest="to_date", help="검색 종료일 (YYYY-MM-DD)")
    parser_search.add_argument("--category", help="카테고리")
    parser_search.add_argument("--type", help="타입 (income/expense 또는 수입/지출)")
    parser_search.add_argument("--q", help="메모 검색어")
    parser_search.add_argument("--tag", help="태그")

    # 4. 월별 요약 (summary)
    parser_sum = subparsers.add_parser("summary", help="월별 요약 및 카테고리 리포트", parents=[parent_parser])
    parser_sum.add_argument("--month", required=True, help="조회할 월 (YYYY-MM)")
    parser_sum.add_argument("--top", type=int, default=3, help="지출 상위 카테고리 개수 (기본값: 3)")

    # 5. 예산 설정 (budget set)
    parser_bud = subparsers.add_parser("budget", help="월별 예산 설정", parents=[parent_parser])
    bud_subparsers = parser_bud.add_subparsers(dest="budget_action", help="예산 동작")
    parser_bud_set = bud_subparsers.add_parser("set", help="월별 예산 저장", parents=[parent_parser])
    parser_bud_set.add_argument("--month", required=True, help="예산 대상 월 (YYYY-MM)")
    parser_bud_set.add_argument("--amount", type=int, required=True, help="예산 금액 (양의 정수)")

    # 6. 카테고리 관리 (category add/list/remove)
    parser_cat = subparsers.add_parser("category", help="카테고리 관리 (add/list/remove)", parents=[parent_parser])
    cat_subparsers = parser_cat.add_subparsers(dest="category_action", help="카테고리 동작")
    
    parser_cat_add = cat_subparsers.add_parser("add", help="카테고리 추가", parents=[parent_parser])
    parser_cat_add.add_argument("name", nargs="?", help="추가할 카테고리명 (생략 시 대화형 입력)")

    cat_subparsers.add_parser("list", help="카테고리 목록 조회", parents=[parent_parser])

    parser_cat_remove = cat_subparsers.add_parser("remove", help="카테고리 삭제", parents=[parent_parser])
    parser_cat_remove.add_argument("name", help="삭제할 카테고리명")

    # 7. 거래 수정 (update) - 옵션 기반
    parser_upd = subparsers.add_parser("update", help="거래 수정 (옵션 기반)", parents=[parent_parser])
    parser_upd.add_argument("--id", required=True, help="수정할 거래 ID")
    parser_upd.add_argument("--date", help="날짜 (YYYY-MM-DD)")
    parser_upd.add_argument("--type", help="타입 (income/expense)")
    parser_upd.add_argument("--category", help="카테고리")
    parser_upd.add_argument("--amount", type=int, help="금액")
    parser_upd.add_argument("--memo", help="메모")
    parser_upd.add_argument("--tags", help="태그 (쉼표 구분)")

    # 8. 거래 삭제 (delete)
    parser_del = subparsers.add_parser("delete", help="거래 삭제", parents=[parent_parser])
    parser_del.add_argument("--id", required=True, help="삭제할 거래 ID")

    # 9. CSV 내보내기 (export)
    parser_exp = subparsers.add_parser("export", help="CSV 내보내기", parents=[parent_parser])
    parser_exp.add_argument("--out", required=True, help="내보낼 CSV 파일 경로")
    parser_exp.add_argument("--month", help="내보낼 대상 월 (YYYY-MM)")
    parser_exp.add_argument("--from", dest="from_date", help="시작일 (YYYY-MM-DD)")
    parser_exp.add_argument("--to", dest="to_date", help="종료일 (YYYY-MM-DD)")

    # 10. CSV 가져오기 (import)
    parser_imp = subparsers.add_parser("import", help="CSV 가져오기", parents=[parent_parser])
    parser_imp.add_argument("--from", dest="from_path", required=True, help="가져올 CSV 파일 경로")

    # 커맨드 라인 인자 파싱
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 데이터 저장소 및 서비스 객체 인스턴스화
    repo = Repository(data_dir=args.data_dir)
    svc = BudgetService(repo)

    # 1. add: 대화형 입력 처리
    if args.command == "add":
        try:
            date_input = input("날짜(YYYY-MM-DD): ").strip()
            svc._validate_date(date_input)

            type_input = input("타입(income/expense): ").strip()
            validated_type = svc._validate_type(type_input)

            category_input = input("카테고리: ").strip()
            svc._validate_category(category_input)

            amount_str = input("금액(양수): ").strip()
            if not amount_str.isdigit():
                raise ValidationError("금액은 양의 정수로 입력해야 합니다.", "예: 15000")
            amount_input = int(amount_str)
            svc._validate_amount(amount_input)

            memo_input = input("메모(선택): ").strip()
            tags_input_str = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
            tags_input = [t.strip() for t in tags_input_str.split(",") if t.strip()] if tags_input_str else []

            tx = svc.add_transaction(
                date=date_input,
                type=validated_type,
                category=category_input,
                amount=amount_input,
                memo=memo_input,
                tags=tags_input
            )
            print(f"[저장 완료] id={tx.id}")
        except KeyboardInterrupt:
            print("\n[취소됨] 거래 추가가 취소되었습니다.")
            sys.exit(1)

    # 2. list: 최신순 스트리밍 출력
    elif args.command == "list":
        for tx in svc.list_transactions(limit=args.limit):
            _print_tx(tx)

    # 3. search: 조건 필터링 스트리밍 출력
    elif args.command == "search":
        for tx in svc.search_transactions(
            from_date=args.from_date,
            to_date=args.to_date,
            category=args.category,
            type=args.type,
            q=args.q,
            tag=args.tag
        ):
            _print_tx(tx)

    # 4. summary: 월별 요약 및 TOP N 지출 출력
    elif args.command == "summary":
        res = svc.get_monthly_summary(month=args.month, top_n=args.top)
        if res.get("status") == "데이터 없음":
            print("데이터 없음")
        else:
            print(f"총 수입: {res['total_income']}원")
            print(f"총 지출: {res['total_expense']}원")
            print(f"잔액: {res['balance']}원")
            if res.get("budget"):
                b = res["budget"]
                warn_str = " [경고: 예산 초과!]" if b["warning"] else ""
                print(f"예산: {b['amount']}원 (사용률 {b['usage_rate']:.1f}%){warn_str}")
            
            top_cats = res.get("top_categories", [])
            if top_cats:
                print(f"\n지출 TOP {len(top_cats)}")
                for idx, (cat, amt) in enumerate(top_cats, 1):
                    print(f"{idx}) {cat} {amt}원")

    # 5. budget: 예산 설정
    elif args.command == "budget":
        if args.budget_action == "set":
            b = svc.set_budget(month=args.month, amount=args.amount)
            print(f"[저장 완료] {b.month} 예산 {b.amount}원")
        else:
            parser_bud.print_help()

    # 6. category: 카테고리 관리
    elif args.command == "category":
        if args.category_action == "list":
            for c in svc.list_categories():
                print(f"- {c.name}")
        elif args.category_action == "add":
            name = args.name
            if not name:
                name = input("카테고리명: ").strip()
            svc.add_category(name)
            print(f"[저장 완료] category={name}")
        elif args.category_action == "remove":
            svc.remove_category(args.name)
            print(f"[삭제 완료] category={args.name}")
        else:
            parser_cat.print_help()

    # 7. update: 거래 정보 수정
    elif args.command == "update":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
        tx = svc.update_transaction(
            id=args.id,
            date=args.date,
            type=args.type,
            category=args.category,
            amount=args.amount,
            memo=args.memo,
            tags=tags
        )
        print(f"[수정 완료] id={tx.id}")

    # 8. delete: 거래 삭제
    elif args.command == "delete":
        svc.delete_transaction(args.id)
        print(f"[삭제 완료] id={args.id}")

    # 9. export: CSV 내보내기
    elif args.command == "export":
        count = svc.export_csv(
            path=args.out,
            month=args.month,
            from_date=args.from_date,
            to_date=args.to_date
        )
        print(f"[완료] {args.out} ({count} records)")

    # 10. import: CSV 가져오기
    elif args.command == "import":
        res = svc.import_csv(args.from_path)
        print(f"[완료] imported={res['imported']}, skipped={res['skipped']}")

if __name__ == "__main__":
    main()
