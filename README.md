# Console Pocket Book (CLI 가계부 애플리케이션)

## 📖 프로젝트 소개
`budget_app`은 커맨드 라인 인터페이스(CLI)에서 동작하는 경량화된 파일 입출력 기반 가계부 애플리케이션입니다. 
빠른 실행 속도, 대용량 파일 스트리밍 처리, 그리고 명확한 계층형 아키텍처 설계를 특징으로 합니다. 
터미널 환경에 최적화되어 직관적이고 쾌적한 사용자 경험(UX)을 제공합니다.

### 🌟 주요 특징
- **스트리밍 아키텍처**: 제너레이터(`yield`)를 사용하여 메모리 초과 없이 대용량 가계부 데이터 처리 (O(1) 메모리 유지)
- **계층형 설계**: CLI, Service, Repository, Model로 책임을 분리하여 높은 유지보수성 확보 (SRP 원칙 준수)
- **사용자 친화적 UX**: 복잡한 파이썬 스택 트레이스를 숨기고, 친절한 `[오류]` 원인과 `[힌트]` 해결책 제공 (POSIX exit code 준수)
- **강력한 데이터 계약**: 타입 힌트와 `dataclass`를 활용하여 안전한 데이터 모델링 및 런타임 유효성 검증
- **안전한 영구 저장**: 임시 파일 작성 후 원자적 교체(`atomic rename`) 방식으로 파일 손상 방지

---

## 🚀 실행 방법
애플리케이션은 모듈 단위로 실행합니다. 프로젝트 루트 디렉터리에서 아래 명령어를 사용하세요.

```bash
python -m budget_app <command> [options]
```

모든 명령어는 `--help` 옵션을 통해 상세 사용법을 확인할 수 있습니다.
```bash
python -m budget_app --help
python -m budget_app <command> --help
```

---

## 📂 데이터 저장 위치 및 형식
모든 데이터는 기본적으로 프로젝트 루트의 `./data/` 폴더 내에 저장되며, `--data-dir <path>` 옵션으로 저장 위치를 변경할 수 있습니다.
각 데이터 항목은 한 줄에 하나의 JSON 객체 형태인 **JSONL (JSON Lines)** 형식으로 영구 보관됩니다.

- **거래 내역 파일**: `./data/transactions.jsonl`
- **카테고리 파일**: `./data/categories.jsonl` (최초 실행 시 `food`, `transport`, `living`, `salary` 등 기본 시드 자동 생성)
- **예산 설정 파일**: `./data/budgets.jsonl`

---

## 💻 주요 명령어 사용법 및 예시

| 명령어 | 형식 | 설명 및 실행 예시 |
|---|---|---|
| **add** | 대화형 입력 | 날짜, 타입, 카테고리, 금액, 메모, 태그를 순차 입력받아 거래 추가<br/>`python -m budget_app add` |
| **list** | 옵션 인자 | 최신순 거래 목록 조회 (스트리밍 처리)<br/>`python -m budget_app list --limit 5` |
| **search** | 옵션 인자 | 기간, 카테고리, 타입, 키워드, 태그 조건 검색<br/>`python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --q 점심` |
| **summary** | 옵션 인자 | 월별 총수입/총지출/잔액, 예산 대비 사용률/초과 경고, 지출 TOP N 카테고리 리포트<br/>`python -m budget_app summary --month 2024-01 --top 3` |
| **budget set** | 옵션 인자 | 월별 목표 예산 금액 설정 및 영구 저장<br/>`python -m budget_app budget set --month 2024-01 --amount 500000` |
| **category list** | CLI 인자 | 등록된 카테고리 목록 조회<br/>`python -m budget_app category list` |
| **category add** | 인자/대화형 | 신규 카테고리 추가<br/>`python -m budget_app category add travel` |
| **category remove** | CLI 인자 | 카테고리 삭제 (거래 내역에 사용 중인 카테고리는 삭제 차단)<br/>`python -m budget_app category remove travel` |
| **update** | 옵션 인자 | 거래 ID 기반 필드 부분 수정<br/>`python -m budget_app update --id TX-000012 --amount 20000 --memo "저녁 식사"` |
| **delete** | 옵션 인자 | 거래 ID 기반 특정 거래 삭제<br/>`python -m budget_app delete --id TX-000012` |
| **export** | 옵션 인자 | 기간 또는 월별 조건에 맞는 거래 데이터를 CSV 파일로 내보내기<br/>`python -m budget_app export --out export.csv --month 2024-01` |
| **import** | 옵션 인자 | CSV 파일로부터 거래 내역 일괄 등록 (성공/실패 건수 출력)<br/>`python -m budget_app import --from import.csv` |

---

## 📊 CSV 입출력 (Import / Export) 스키마

`import` 및 `export` 명령어 사용 시 적용되는 CSV 표준 스키마입니다. (UTF-8 인코딩, 첫 번째 줄 헤더 포함)

| column | required | 설명 | 예시 |
|---|:---:|---|---|
| **date** | Y | 거래 일자 (YYYY-MM-DD) | `2024-01-15` |
| **type** | Y | 거래 유형 (`income` 또는 `expense`, `수입`/`지출` 호환) | `expense` |
| **category** | Y | 등록된 카테고리명 | `food` |
| **amount** | Y | 양의 정수 금액 | `15000` |
| **memo** | N | 메모 내용 (문자열) | `점심 식사` |
| **tags** | N | 쉼표(`,`)로 구분된 태그 목록 | `meal,lunch` |

---

## 📚 학습 가이드 목차 안내 (탑다운 학습)
본 프로젝트는 **구현 후 학습하는 탑다운(Top-down) 방식**을 위해 심화 개념 학습 가이드를 제공합니다.  
`docs/learning/` 디렉터리의 문서를 통해 실제 구현 코드와 함께 소프트웨어 공학 핵심 역량을 학습할 수 있습니다.

1. [**계층형 아키텍처 (Layered Architecture)**](./docs/learning/01_layered_architecture.md): CLI $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ Models의 역할 및 책임 분리(SRP), 낮은 결합도 설계
2. [**제너레이터 스트리밍 (Generator Streaming)**](./docs/learning/02_generator_streaming.md): `yield`를 통한 $O(1)$ 메모리 효율성, 대용량 파일 스트리밍 파이프라인 처리
3. [**데코레이터 패턴 (Decorators)**](./docs/learning/03_decorators.md): 공통 관심사(로깅, 실행 시간 측정, 예외 래핑) 분리 원리 및 `@functools.wraps`
4. [**타입 힌트와 Dataclass**](./docs/learning/04_type_hints_and_dataclass.md): Python 3.10+ 타입 힌트와 `dataclass`를 통한 견고한 데이터 계약(Contract) 설계
5. [**에러 핸들링과 CLI UX**](./docs/learning/05_error_handling_and_cli.md): 스택 트레이스 숨김, `[오류]` 원인 + `[힌트]` 해결책 패턴, POSIX exit code 규격
