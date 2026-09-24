import argparse
import sys
from budget_app.repository import Repository
from budget_app.services import BudgetService
from budget_app.decorators import handle_cli_error
from budget_app.exceptions import ValidationError

def _print_tx(tx):
    memo_str = tx.memo if tx.memo else ""
    print(f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount} | {memo_str}")

@handle_cli_error
def main(argv=None):
    # Common parent parser for global options
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--data-dir", default="./data", help="데이터 저장 디렉터리 (기본값: ./data)")

    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="콘솔 용돈 기입장 (가계부) 프로그램",
        parents=[parent_parser]
    )
    
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어")

    # 1. add
    subparsers.add_parser("add", help="거래 추가 (대화형 입력)", parents=[parent_parser])

    # 2. list
    parser_list = subparsers.add_parser("list", help="거래 목록 조회 (최신순)", parents=[parent_parser])
    parser_list.add_argument("--limit", type=int, help="출력할 거래 건수")

    # 3. search
    parser_search = subparsers.add_parser("search", help="거래 검색", parents=[parent_parser])
    parser_search.add_argument("--from", dest="from_date", help="검색 시작일 (YYYY-MM-DD)")
    parser_search.add_argument("--to", dest="to_date", help="검색 종료일 (YYYY-MM-DD)")
    parser_search.add_argument("--category", help="카테고리")
    parser_search.add_argument("--type", help="타입 (income/expense 또는 수입/지출)")
    parser_search.add_argument("--q", help="메모 검색어")
    parser_search.add_argument("--tag", help="태그")

    # 4. summary
    parser_sum = subparsers.add_parser("summary", help="월별 요약 및 카테고리 리포트", parents=[parent_parser])
    parser_sum.add_argument("--month", required=True, help="조회할 월 (YYYY-MM)")
    parser_sum.add_argument("--top", type=int, default=3, help="지출 상위 카테고리 개수 (기본값: 3)")

    # 5. budget
    parser_bud = subparsers.add_parser("budget", help="월별 예산 설정", parents=[parent_parser])
    bud_subparsers = parser_bud.add_subparsers(dest="budget_action", help="예산 동작")
    parser_bud_set = bud_subparsers.add_parser("set", help="월별 예산 저장", parents=[parent_parser])
    parser_bud_set.add_argument("--month", required=True, help="예산 대상 월 (YYYY-MM)")
    parser_bud_set.add_argument("--amount", type=int, required=True, help="예산 금액 (양의 정수)")

    # 6. category
    parser_cat = subparsers.add_parser("category", help="카테고리 관리 (add/list/remove)", parents=[parent_parser])
    cat_subparsers = parser_cat.add_subparsers(dest="category_action", help="카테고리 동작")
    
    parser_cat_add = cat_subparsers.add_parser("add", help="카테고리 추가", parents=[parent_parser])
    parser_cat_add.add_argument("name", nargs="?", help="추가할 카테고리명 (생략 시 대화형 입력)")

    cat_subparsers.add_parser("list", help="카테고리 목록 조회", parents=[parent_parser])

    parser_cat_remove = cat_subparsers.add_parser("remove", help="카테고리 삭제", parents=[parent_parser])
    parser_cat_remove.add_argument("name", help="삭제할 카테고리명")

    # 7. update
    parser_upd = subparsers.add_parser("update", help="거래 수정 (옵션 기반)", parents=[parent_parser])
    parser_upd.add_argument("--id", required=True, help="수정할 거래 ID")
    parser_upd.add_argument("--date", help="날짜 (YYYY-MM-DD)")
    parser_upd.add_argument("--type", help="타입 (income/expense)")
    parser_upd.add_argument("--category", help="카테고리")
    parser_upd.add_argument("--amount", type=int, help="금액")
    parser_upd.add_argument("--memo", help="메모")
    parser_upd.add_argument("--tags", help="태그 (쉼표 구분)")

    # 8. delete
    parser_del = subparsers.add_parser("delete", help="거래 삭제", parents=[parent_parser])
    parser_del.add_argument("--id", required=True, help="삭제할 거래 ID")

    # 9. export
    parser_exp = subparsers.add_parser("export", help="CSV 내보내기", parents=[parent_parser])
    parser_exp.add_argument("--out", required=True, help="내보낼 CSV 파일 경로")
    parser_exp.add_argument("--month", help="내보낼 대상 월 (YYYY-MM)")
    parser_exp.add_argument("--from", dest="from_date", help="시작일 (YYYY-MM-DD)")
    parser_exp.add_argument("--to", dest="to_date", help="종료일 (YYYY-MM-DD)")

    # 10. import
    parser_imp = subparsers.add_parser("import", help="CSV 가져오기", parents=[parent_parser])
    parser_imp.add_argument("--from", dest="from_path", required=True, help="가져올 CSV 파일 경로")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(0)

    repo = Repository(data_dir=args.data_dir)
    svc = BudgetService(repo)

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

    elif args.command == "list":
        for tx in svc.list_transactions(limit=args.limit):
            _print_tx(tx)

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

    elif args.command == "budget":
        if args.budget_action == "set":
            b = svc.set_budget(month=args.month, amount=args.amount)
            print(f"[저장 완료] {b.month} 예산 {b.amount}원")
        else:
            parser_bud.print_help()

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

    elif args.command == "delete":
        svc.delete_transaction(args.id)
        print(f"[삭제 완료] id={args.id}")

    elif args.command == "export":
        count = svc.export_csv(
            path=args.out,
            month=args.month,
            from_date=args.from_date,
            to_date=args.to_date
        )
        print(f"[완료] {args.out} ({count} records)")

    elif args.command == "import":
        res = svc.import_csv(args.from_path)
        print(f"[완료] imported={res['imported']}, skipped={res['skipped']}")

if __name__ == "__main__":
    main()
