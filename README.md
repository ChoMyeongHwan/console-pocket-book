# Console Pocket Book (CLI 가계부 애플리케이션)

## 📖 프로젝트 소개
`budget_app`은 커맨드 라인 인터페이스(CLI)에서 동작하는 경량화된 파일 입출력 기반 가계부 애플리케이션입니다. 
빠른 실행 속도, 대용량 파일 스트리밍 처리, 그리고 명확한 계층형 아키텍처 설계를 특징으로 합니다. 
터미널 환경에 최적화되어 직관적이고 쾌적한 사용자 경험(UX)을 제공합니다.

---

## 🏗️ 모듈별 책임 및 파일 매핑 구조 (PASS #8 보완)

단일 책임 원칙(SRP)에 따라 각 모듈의 역할을 엄격히 분리하였습니다.

| 파일명 | 계층 (Layer) | 핵심 책임 및 역할 (1문장 요약) |
|---|:---:|---|
| [`budget_app/__main__.py`](./budget_app/__main__.py) | Entry Point | `python -m budget_app` 실행 시 CLI 메인 함수를 호출하는 모듈 진입점 |
| [`budget_app/cli.py`](./budget_app/cli.py) | Presentation | `argparse` 기반 명령어 파싱, 대화형 콘솔 입출력 처리 및 포맷팅 |
| [`budget_app/services.py`](./budget_app/services.py) | Business Logic | 거래 CRUD, 예산 분석, 카테고리 무결성, CSV 입출력 등 핵심 규칙 총괄 |
| [`budget_app/repository.py`](./budget_app/repository.py) | Persistence | JSONL 파일 영구 저장, `yield` 제너레이터 스트리밍 및 원자적 교체 I/O |
| [`budget_app/models.py`](./budget_app/models.py) | Domain Model | `dataclass` 기반 거래/카테고리/예산 불변 조건 및 고유 ID 채번 계약 정의 |
| [`budget_app/exceptions.py`](./budget_app/exceptions.py) | Exception | 세분화된 POSIX 종료 코드와 원인/힌트를 갖춘 비즈니스 예외 계층 정의 |
| [`budget_app/decorators.py`](./budget_app/decorators.py) | Cross-Cutting | 스택트레이스 은닉, 디버그 토글, 시간 측정, 감사 로깅 등 공통 관심사 분리 |

---

## ⚖️ JSONL vs CSV 저장 포맷 비교 및 선정 근거 (FAIL #14 보완)

과제 요구사항에 따라 내부 영구 저장 포맷을 비교 분석 후 **JSONL(JSON Lines)**을 최종 선정하였습니다. (외부 연동은 규격대로 CSV 처리)

| 비교 항목 | JSONL (선정됨) | CSV | 선정 근거 |
|---|---|---|---|
| **스트리밍 친화성** | 줄 단위 `json.loads`로 완벽한 $O(1)$ 스트리밍 가능 | 복합 텍스트(줄바꿈/따옴표) 처리 시 파싱 오버헤드 존재 | 제너레이터 메모리 최적화에 JSONL이 가장 적합 |
| **복합 데이터 지원** | `tags: ["외식", "점심"]` 등 리스트/중첩 객체 기본 지원 | 쉼표 구분 문자열 파싱 등 별도 직렬화 규칙 필요 | 데이터 모델의 풍부한 표현력 보장 |
| **스키마 유연성** | 필드 추가/선택적 필드(`memo`) 누락 시에도 무결성 유지 | 컬럼 순서 및 개수가 강제되어 확장에 취약 | 향후 기능 확장성 우수 |
| **원자적 갱신성** | 행 단위의 명확한 독립성으로 손상 범위 최소화 | 헤더 및 인코딩 종속성 높음 | 원자적 교체(`atomic rename`)와 궁합 우수 |

---

## 📂 데이터 저장 위치 및 파일 보존 메커니즘 (PASS #2, #10 보완)

모든 데이터는 기본적으로 프로젝트 루트의 `./data/` 폴더 내에 분리 저장되며, 프로그램 재실행 시에도 데이터가 완벽히 보존됩니다.

```text
console-pocket-book/
└── data/
    ├── transactions.jsonl  # 거래 내역 (고유 ID, 일자, 타입, 카테고리, 금액, 메모, 태그)
    ├── categories.jsonl    # 카테고리 목록 (기초 8종 자동 시드 및 사용자 추가 목록)
    └── budgets.jsonl       # 월별 목표 예산 금액 설정
```

* **원자적 쓰기 및 자동 롤백 정책**:
  - `repository.py`는 데이터 저장 시 먼저 임시 파일(`tempfile.mkstemp`)에 모든 내용을 기록합니다.
  - 기록 도중 디스크 오류나 비정상 종료 발생 시: **임시 파일은 즉시 삭제(`unlink`)되고 기존 파일은 100% 보존(자동 롤백)**됩니다.
  - 정상 기록 완료 시: OS의 원자적 연산인 `os.replace`로 순간 교체되어 파일 손상을 방지합니다.

---

## 🚀 실행 방법 및 옵션 체계

```bash
# 기본 모듈 실행
python -m budget_app <command> [options]

# 도움말 확인
python -m budget_app --help
python -m budget_app <command> --help

# 디버그 모드 실행 (상세 스택트레이스 및 에러 출력) (PASS #6 보완)
python -m budget_app --debug <command> [options]
# 또는 환경변수 설정: export BUDGET_APP_DEBUG=1
```

---

## 💻 주요 명령어 사용법

| 명령어 | 형식 | 설명 및 실행 예시 |
|---|---|---|
| **add** | 대화형 입력 | 날짜, 타입, 카테고리, 금액, 메모, 태그 순차 입력<br/>`python -m budget_app add` |
| **list** | 옵션 인자 | 최신순 거래 목록 스트리밍 출력<br/>`python -m budget_app list --limit 5` |
| **search** | 옵션 인자 | 다중 조건 필터링 검색<br/>`python -m budget_app search --category food --q 점심` |
| **summary** | 옵션 인자 | 월별 재정 요약, TOP N 지출, 예산 경고<br/>`python -m budget_app summary --month 2024-01 --top 3` |
| **budget set** | 옵션 인자 | 월별 목표 예산 저장<br/>`python -m budget_app budget set --month 2024-01 --amount 500000` |
| **category list** | CLI 인자 | 등록된 카테고리 목록 조회<br/>`python -m budget_app category list` |
| **category add** | 인자/대화형 | 신규 카테고리 등록<br/>`python -m budget_app category add travel` |
| **category remove** | CLI 인자 | 카테고리 삭제 (대체 이전 옵션 지원)<br/>`python -m budget_app category remove travel --replace-with food` |
| **update** | 옵션 인자 | 거래 필드 부분 수정<br/>`python -m budget_app update --id TX-000012 --amount 20000` |
| **delete** | 옵션 인자 | 거래 삭제<br/>`python -m budget_app delete --id TX-000012` |
| **export** | 옵션 인자 | 조건별 CSV 내보내기<br/>`python -m budget_app export --out export.csv --month 2024-01` |
| **import** | 옵션 인자 | CSV 일괄 가져오기 (오류 행 스킵 상세 리포트)<br/>`python -m budget_app import --from import.csv` |

---

## 🔔 예산 초과 알림 및 확장 포인트 (PASS #4 보완)

월별 요약(`summary`) 실행 시 목표 예산과 실제 지출을 비교하여 다단계 알림을 출력합니다.

* **출력 포맷 및 경고 레벨**:
  - `NORMAL` (사용률 < 80%): `예산: 500,000원 (사용률 45.0%)`
  - `CAUTION` (80% $\le$ 사용률 $\le$ 100%): `예산: 500,000원 (사용률 85.0%) [주의: 예산 80% 이상 소진]`
  - `DANGER` (사용률 > 100%): `예산: 500,000원 (사용률 110.0%) [경고: 예산 초과!]`
* **확장 옵션**: `--threshold <float>` 옵션을 통해 경고 임계치를 동적으로 변경할 수 있습니다 (예: `--threshold 90.0`).

---

## 🚦 POSIX 종료 코드(Exit Code) 매핑 표 (PASS #7 보완)

스크립트 연동 및 자동화 파이프라인을 위해 오류 유형별 세분화된 종료 코드를 제공합니다.

| Exit Code | 예외 클래스 | 발생 상황 | 사용자 화면 메시지 예시 |
|:---:|---|---|---|
| **0** | - | 정상 실행 완료 | `[저장 완료] id=TX-XXXXXX` |
| **1** | `BudgetAppError` | 일반 런타임 오류 또는 알 수 없는 예외 | `[오류] 알 수 없는 오류가 발생했습니다` |
| **2** | `ValidationError` | 날짜 형식 오류, 음수 금액, 미등록 카테고리 등 | `[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).` |
| **3** | `NotFoundError` | 존재하지 않는 거래 ID 조회/수정/삭제 시 | `[오류] ID 'TX-NOTFOUND'에 해당하는 거래를 찾을 수 없습니다.` |
| **4** | `DataStoreError` | 파일 읽기/쓰기 권한 및 디스크 I/O 오류 시 | `[오류] 파일 저장 중 오류가 발생했습니다` |

---

## 🧩 공통 관심사 데코레이터 동작 및 부작용(Side Effects) (PASS #12 보완)

| 데코레이터 | 핵심 동작 | 부작용 (Side Effects) |
|---|---|---|
| **`@handle_cli_error`** | CLI 실행 중 발생하는 비즈니스/시스템 예외 가로채기 | 스택트레이스를 은닉하고 사용자 힌트 출력 후 `sys.exit(exit_code)`로 프로세스 강제 종료 |
| **`@measure_execution_time`** | 비즈니스 로직 함수의 순수 수행 시간 정밀 측정 | 환경변수 `BUDGET_APP_PROFILE=1` 또는 디버그 모드 시 `stderr`에 소요 시간 출력 |
| **`@log_action`** | 데이터 변경(CUD) 이벤트 감지 및 감사 로그 작성 | 환경변수 `BUDGET_APP_AUDIT=1` 활성화 시 메서드 호출 내역을 감사 로그 스트림에 출력 |

---

## 📊 CSV 입출력 표준 스키마

`import` 및 `export` 명령어 사용 시 적용되는 UTF-8 CSV 스키마입니다.

| column | required | 설명 | 예시 |
|---|:---:|---|---|
| **date** | Y | 거래 일자 (YYYY-MM-DD) | `2024-01-15` |
| **type** | Y | 거래 유형 (`income` 또는 `expense`, `수입`/`지출` 호환) | `expense` |
| **category** | Y | 등록된 카테고리명 | `food` |
| **amount** | Y | 양의 정수 금액 | `15000` |
| **memo** | N | 메모 내용 (문자열) | `점심 식사` |
| **tags** | N | 쉼표(`,`) 구분 태그 목록 | `meal,lunch` |

---

## 📚 심화 문서 및 학습 가이드 목차

본 프로젝트는 설계 원리와 실전 시연을 체계적으로 검증할 수 있는 심화 문서들을 제공합니다:

1. [**기능별 1:1 실행 증거 문서 (EXECUTION_EVIDENCE.md)**](./docs/EXECUTION_EVIDENCE.md) - 10대 핵심 기능 실행 캡처 입증 (FAIL #1 보완)
2. [**대용량 100k+ 병목 분석 및 개선안 (LARGE_SCALE_ANALYSIS.md)**](./docs/LARGE_SCALE_ANALYSIS.md) - 대용량 정렬 및 I/O 병목 아키텍처 분석 (FAIL #15 보완)
3. [**CSV 부분 임포트 정책 문서 (IMPORT_POLICY.md)**](./docs/IMPORT_POLICY.md) - Best-Effort 전략 및 스킵 상세 리포트 규격 (FAIL #16 보완)
4. [**카테고리 수명주기 및 참조 무결성 정책 (CATEGORY_POLICY.md)**](./docs/CATEGORY_POLICY.md) - 기본 카테고리 보호 및 대체 마이그레이션 정책 (PASS #3 보완)
5. [**과제 평가 시연 시나리오 (DEMO_SCENARIO.md)**](./docs/DEMO_SCENARIO.md) - 평가자 앞 실전 10단계 시연 스크립트 및 예상 Q&A
6. [**탑다운 심화 학습 가이드 5종 (docs/learning/)**](./docs/learning/):
   - [`01_layered_architecture.md`](./docs/learning/01_layered_architecture.md): 계층형 설계 및 SRP
   - [`02_generator_streaming.md`](./docs/learning/02_generator_streaming.md): `yield` O(1) 메모리 최적화
   - [`03_decorators.md`](./docs/learning/03_decorators.md): 데코레이터 패턴과 공통 관심사 분리
   - [`04_type_hints_and_dataclass.md`](./docs/learning/04_type_hints_and_dataclass.md): 데이터 계약과 정적/동적 검증
   - [`05_error_handling_and_cli.md`](./docs/learning/05_error_handling_and_cli.md): CLI UX 및 POSIX exit code
