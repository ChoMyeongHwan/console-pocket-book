import argparse
import sys
from budget_app.repository import Repository
from budget_app.services import BudgetService
from budget_app.decorators import handle_cli_error

def _print_tx(tx):
    print(f"[{tx.id}] {tx.date} | {tx.type} | {tx.category} | {tx.amount}원 | {tx.memo} | tags: {','.join(tx.tags)}")

@handle_cli_error
def main():
    parser = argparse.ArgumentParser(prog="budget_app", description="Console Pocket Book")
    parser.add_argument("--data-dir", default="./data", help="데이터 저장 디렉터리")
    
    subparsers = parser.add_subparsers(dest="command", help="명령어")
    
    # add
    parser_add = subparsers.add_parser("add", help="거래 내역 추가 (대화형)")
    
    # list
    parser_list = subparsers.add_parser("list", help="최신순 조회")
    parser_list.add_argument("--limit", type=int, help="조회할 최대 개수")
    
    # search
    parser_search = subparsers.add_parser("search", help="검색")
    parser_search.add_argument("--from", dest="from_date", help="시작일 (YYYY-MM-DD)")
    parser_search.add_argument("--to", dest="to_date", help="종료일 (YYYY-MM-DD)")
    parser_search.add_argument("--category", help="카테고리")
    parser_search.add_argument("--type", help="유형 (수입/지출)")
    parser_search.add_argument("--q", help="메모 검색어")
    parser_search.add_argument("--tags", dest="tag", help="태그")
    
    # update
    parser_upd = subparsers.add_parser("update", help="수정")
    parser_upd.add_argument("--id", required=True, help="거래 ID")
    parser_upd.add_argument("--date", help="날짜")
    parser_upd.add_argument("--type", help="유형")
    parser_upd.add_argument("--category", help="카테고리")
    parser_upd.add_argument("--amount", type=int, help="금액")
    parser_upd.add_argument("--memo", help="메모")
    parser_upd.add_argument("--tags", help="태그 쉼표 구분")
    
    # delete
    parser_del = subparsers.add_parser("delete", help="삭제")
    parser_del.add_argument("--id", required=True, help="거래 ID")
    
    # category
    parser_cat = subparsers.add_parser("category", help="카테고리 관리")
    parser_cat.add_argument("action", choices=["list", "add", "remove"])
    parser_cat.add_argument("name", nargs="?", help="카테고리 이름")
    
    # budget
    parser_bud = subparsers.add_parser("budget", help="예산 관리")
    parser_bud.add_argument("action", choices=["set", "summary"])
    parser_bud.add_argument("--month", help="YYYY-MM")
    parser_bud.add_argument("--amount", type=int, help="예산 금액")
    parser_bud.add_argument("--top", type=int, default=3, help="Top N")
    
    # export
    parser_exp = subparsers.add_parser("export", help="CSV 내보내기")
    parser_exp.add_argument("--out", required=True, help="경로")
    parser_exp.add_argument("--month", help="YYYY-MM")
    parser_exp.add_argument("--from", dest="from_date", help="시작일")
    parser_exp.add_argument("--to", dest="to_date", help="종료일")
    
    # import
    parser_imp = subparsers.add_parser("import", help="CSV 가져오기")
    parser_imp.add_argument("--file", required=True, help="경로")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    repo = Repository(data_dir=args.data_dir)
    svc = BudgetService(repo)

    if args.command == "add":
        try:
            date = input("날짜 (YYYY-MM-DD): ").strip()
            type_str = input("유형 (수입/지출): ").strip()
            category = input("카테고리: ").strip()
            amount_str = input("금액: ").strip()
            amount = int(amount_str) if amount_str.isdigit() else 0
            memo = input("메모: ").strip()
            tags_str = input("태그 (쉼표 구분): ").strip()
            tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
            
            tx = svc.add_transaction(date, type_str, category, amount, memo, tags)
            print("거래가 추가되었습니다.")
            _print_tx(tx)
        except KeyboardInterrupt:
            print("\n취소되었습니다.")
            sys.exit(1)
            
    elif args.command == "list":
        for tx in svc.list_transactions(limit=args.limit):
            _print_tx(tx)
            
    elif args.command == "search":
        for tx in svc.search_transactions(args.from_date, args.to_date, args.category, args.type, args.q, args.tag):
            _print_tx(tx)
            
    elif args.command == "update":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        tx = svc.update_transaction(args.id, args.date, args.type, args.category, args.amount, args.memo, tags)
        print("거래가 수정되었습니다.")
        _print_tx(tx)
        
    elif args.command == "delete":
        svc.delete_transaction(args.id)
        print("거래가 삭제되었습니다.")
        
    elif args.command == "category":
        if args.action == "list":
            for c in svc.list_categories():
                print(f"{c.name} {'(기본)' if c.is_default else ''}")
        elif args.action == "add":
            if not args.name:
                print("이름을 입력하세요.")
                sys.exit(1)
            svc.add_category(args.name)
            print(f"카테고리 '{args.name}' 추가됨")
        elif args.action == "remove":
            if not args.name:
                print("이름을 입력하세요.")
                sys.exit(1)
            svc.remove_category(args.name)
            print(f"카테고리 '{args.name}' 삭제됨")
            
    elif args.command == "budget":
        if not args.month:
            print("--month (YYYY-MM)가 필요합니다.")
            sys.exit(1)
            
        if args.action == "set":
            if not args.amount:
                print("--amount 가 필요합니다.")
                sys.exit(1)
            svc.set_budget(args.month, args.amount)
            print("예산이 설정되었습니다.")
            
        elif args.action == "summary":
            res = svc.get_monthly_summary(args.month, args.top)
            if res["status"] == "데이터 없음":
                print("데이터 없음")
            else:
                print(f"총 수입: {res['total_income']}원")
                print(f"총 지출: {res['total_expense']}원")
                print(f"잔액: {res['balance']}원")
                print("지출 Top 카테고리:")
                for k, v in res['top_categories']:
                    print(f"  - {k}: {v}원")
                if res['budget']:
                    print(f"예산 사용률: {res['budget']['usage_rate']:.1f}%")
                    if res['budget']['warning']:
                        print("경고: 예산을 초과했습니다!")
                        
    elif args.command == "export":
        svc.export_csv(args.out, args.month, args.from_date, args.to_date)
        print("내보내기 완료.")
        
    elif args.command == "import":
        res = svc.import_csv(args.file)
        print(f"가져오기 완료: 성공 {res['imported']}건, 실패 {res['skipped']}건")

if __name__ == "__main__":
    main()
