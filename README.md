# Console Pocket Book (CLI 가계부 애플리케이션)

## 📖 프로젝트 소개
`budget_app`은 커맨드 라인 인터페이스(CLI)에서 동작하는 경량화된 가계부 애플리케이션입니다. 
빠른 실행 속도, 대용량 파일 스트리밍 처리, 그리고 명확한 계층형 아키텍처 설계를 특징으로 합니다. 
터미널 환경에 최적화되어 직관적이고 쾌적한 사용자 경험(UX)을 제공합니다.

### 🌟 주요 특징
- **스트리밍 아키텍처**: 제너레이터(`yield`)를 사용하여 메모리 초과 없이 대용량 가계부 데이터 처리 (O(1) 메모리 유지)
- **계층형 설계**: CLI, Service, Repository, Model로 책임을 분리하여 높은 유지보수성 확보
- **사용자 친화적 UX**: 복잡한 파이썬 스택 트레이스를 숨기고, 친절한 오류 원인과 해결 힌트 제공
- **강력한 데이터 계약**: 타입 힌트와 `dataclass`를 활용하여 안전한 데이터 모델링

---

## 🚀 실행 방법
애플리케이션은 모듈 단위로 실행합니다. 프로젝트 루트 디렉터리에서 아래 명령어를 사용하세요.

```bash
python -m budget_app <command> [options]
```

---

## 📂 데이터 저장 위치 및 형식
모든 데이터는 프로젝트 루트 디렉터리 하위의 `data/` 폴더 내에 저장됩니다.
각 데이터 항목은 한 줄에 하나의 JSON 객체 형태인 **JSONL (JSON Lines)** 형식으로 기록됩니다.

- **거래 내역**: `./data/transactions.jsonl`
- **카테고리**: `./data/categories.jsonl`
- **예산**: `./data/budgets.jsonl`

---

## 💻 주요 명령어 사용법 및 예시

| 명령어 | 설명 | 실행 예시 |
|--------|------|-----------|
| `add` | 새로운 수입/지출 내역을 추가합니다. | `python -m budget_app add --date 2023-10-01 --type 지출 --category 식비 --amount 15000 --memo "점심식사"` |
| `list` | 거래 내역을 전체 또는 특정 월 단위로 조회합니다. | `python -m budget_app list --month 2023-10` |
| `search` | 키워드, 카테고리 등을 조건으로 내역을 검색합니다. | `python -m budget_app search --keyword "커피"` |
| `summary` | 특정 기간의 수입/지출/잔액 요약 통계를 보여줍니다. | `python -m budget_app summary --month 2023-10` |
| `budget` | 월별 예산을 설정하거나 확인합니다. | `python -m budget_app budget set --month 2023-10 --amount 500000` |
| `category` | 사용자 정의 카테고리를 추가, 목록 조회합니다. | `python -m budget_app category list` |
| `update` | 기존 거래 내역을 수정합니다. | `python -m budget_app update <TX_ID> --amount 18000` |
| `delete` | 기존 거래 내역을 삭제합니다. | `python -m budget_app delete <TX_ID>` |
| `import` | 외부 CSV 파일을 읽어와 가계부 데이터로 가져옵니다. | `python -m budget_app import --file ./export.csv` |
| `export` | 가계부 데이터를 CSV 파일로 내보냅니다. | `python -m budget_app export --file ./export.csv` |

---

## 📊 CSV 입출력 (Import / Export) 스키마

`import` 및 `export` 명령어 사용 시, CSV 파일은 아래의 스키마 구조를 반드시 따라야 합니다. 헤더 행이 포함되어야 합니다.

| 컬럼명 | 타입 | 필수 여부 | 설명 및 예시 |
|---|---|---|---|
| **date** | String | 필수 | 거래 날짜 (예: `2023-10-01`) |
| **type** | String | 필수 | 분류 (수입 또는 지출) |
| **category** | String | 필수 | 카테고리명 (예: 식비, 월급 등) |
| **amount** | Integer | 필수 | 금액 (예: `15000`) |
| **memo** | String | 선택 | 메모 내용 (빈 문자열 가능) |
| **tags** | String | 선택 | 태그 목록, 쉼표(`,`)로 구분 (예: `점심,회식`) |

---

## 📚 학습 가이드 목차 안내
본 프로젝트는 탑다운(Top-down) 방식의 교육 목적으로 심화 학습 가이드를 제공합니다.  
`docs/learning/` 디렉터리에 있는 아래의 문서를 통해 소프트웨어 설계 및 파이썬 심화 개념을 학습해보세요!

1. [**계층형 아키텍처**](./docs/learning/01_layered_architecture.md): CLI -> Service -> Repository -> Models의 역할 및 책임 분리(SRP)
2. [**제너레이터 스트리밍**](./docs/learning/02_generator_streaming.md): `yield`를 통한 O(1) 메모리 효율성 및 파이프라인 처리
3. [**데코레이터 패턴**](./docs/learning/03_decorators.md): 공통 관심사(로깅, 실행 시간, 예외) 분리 원리 및 `@functools.wraps`
4. [**타입 힌트와 Dataclass**](./docs/learning/04_type_hints_and_dataclass.md): Python 3.10+ 타입 힌트와 강력한 데이터 계약(Contract) 설계
5. [**에러 핸들링과 CLI UX**](./docs/learning/05_error_handling_and_cli.md): 스택 트레이스 숨김, 해결 힌트 제공, POSIX exit code 규격
