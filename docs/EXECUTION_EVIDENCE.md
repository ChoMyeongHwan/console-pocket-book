# 📸 가계부 프로그램(budget_app) 기능별 1:1 실행 증거 문서 (Execution Evidence)

> **문서 개요**: 본 문서는 네이토 사전평가 항목 #1(기능 실행 증거 부족)을 보완하기 위해, `budget_app`의 10대 핵심 기능(`add`, `list`, `search`, `summary`, `budget`, `category`, `update`, `delete`, `export`, `import`)과 예외 처리 동작을 **실제 터미널 실행 로그 및 단일 명령 입출력 캡처** 로 1:1 입증하는 공식 증빙 자료입니다.

---

## 📑 기능별 실행 증빙 목차

1. [기능 1: 거래 추가 (add) - 대화형 정상 등록 & 유효성 검증 오류](#1-거래-추가-add---대화형-정상-등록--유효성-검증-오류)
2. [기능 2: 거래 목록 조회 (list) - 최신순 정렬 & 스트리밍](#2-거래-목록-조회-list---최신순-정렬--스트리밍)
3. [기능 3: 거래 검색 (search) - 다중 조건 필터링](#3-거래-검색-search---다중-조건-필터링)
4. [기능 4: 월별 요약 (summary) - 통계 산출 & 데이터 없음 처리](#4-월별-요약-summary---통계-산출--데이터-없음-처리)
5. [기능 5: 예산 설정 및 초과 경고 (budget set & summary)](#5-예산-설정-및-초과-경고-budget-set--summary)
6. [기능 6: 카테고리 관리 (category add/list/remove) & 무결성 보호](#6-카테고리-관리-category-addlistremove--무결성-보호)
7. [기능 7: 거래 수정 (update) - 옵션 기반 부분 수정](#7-거래-수정-update---옵션-기반-부분-수정)
8. [기능 8: 거래 삭제 (delete) - ID 기반 삭제 & 없는 ID 처리](#8-거래-삭제-delete---id-기반-삭제--없는-id-처리)
9. [기능 9: CSV 내보내기 (export) - 스키마 준수 및 건수 출력](#9-csv-내보내기-export---스키마-준수-및-건수-출력)
10. [기능 10: CSV 가져오기 (import) - 부분 임포트 & 스킵 상세 리포트](#10-csv-가져오기-import---부분-임포트--스킵-상세-리포트)

---

### 1. 거래 추가 (add) - 대화형 정상 등록 & 유효성 검증 오류

#### 1-1. 정상 등록 실행
```bash
$ python3 -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심 식사
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-D1C6F4
```
* **결과 입증**: 고유 식별자(`TX-XXXXXX`)가 자동 채번되어 `./data/transactions.jsonl`에 정상 기록됨.

#### 1-2. 잘못된 날짜 형식 입력 시 즉시 오류 처리 (스택트레이스 숨김)
```bash
$ python3 -m budget_app add
날짜(YYYY-MM-DD): 2024-13-40
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
$ echo $?
2
```
* **결과 입증**: 스택트레이스를 노출하지 않고 명확한 원인과 힌트를 출력하며 `exit code 2`(ValidationError)로 안전 종료됨.

---

### 2. 거래 목록 조회 (list) - 최신순 정렬 & 스트리밍

```bash
$ python3 -m budget_app list --limit 3
TX-010013 | 2024-01-31 | expense | food | 25000 | 카페 음료 및 디저트
TX-010012 | 2024-01-30 | expense | transport | 25000 | 야근 후 택시 귀가
TX-010011 | 2024-01-28 | expense | food | 55000 | 주말 가족 외식
```
* **결과 입증**: 거래 일자 기준 최신순(내림차순) 정렬되어 출력되며, `--limit` 건수 제한이 적용됨. 내부적으로 `yield` 제너레이터 스트리밍 소비.

---

### 3. 거래 검색 (search) - 다중 조건 필터링

#### 3-1. 카테고리 및 메모 키워드 검색
```bash
$ python3 -m budget_app search --category food --q 장보기
TX-010003 | 2024-01-12 | expense | food | 125000 | 주말 이마트 장보기
```

#### 3-2. 수입 유형만 검색
```bash
$ python3 -m budget_app search --type income
TX-010007 | 2024-01-20 | income | etc | 50000 | 중고 물품 판매 대금
TX-010002 | 2024-01-10 | income | salary | 3200000 | 1월 급여 입금
```
* **결과 입증**: `--category`, `--type`, `--q`, `--from`, `--to`, `--tag` 조건이 결합되어 실시간 필터링됨.

---

### 4. 월별 요약 (summary) - 통계 산출 & 데이터 없음 처리

#### 4-1. 내역이 존재하는 월 조회
```bash
$ python3 -m budget_app summary --month 2024-01 --top 3
총 수입: 3250000원
총 지출: 1230000원
잔액: 2020000원
예산: 1500000원 (사용률 82.0%) [주의: 예산 80% 이상 소진]

지출 TOP 3
1) shopping 450000원
2) living 400000원
3) food 220000원
```

#### 4-2. 내역이 없는 월 조회
```bash
$ python3 -m budget_app summary --month 2024-02
데이터 없음
```
* **결과 입증**: 수입, 지출, 잔액의 정확한 계산 및 데이터 부재 시 "데이터 없음" 문구가 명확히 출력됨.

---

### 5. 예산 설정 및 초과 경고 (budget set & summary)

#### 5-1. 목표 예산 저장
```bash
$ python3 -m budget_app budget set --month 2024-01 --amount 1500000
[저장 완료] 2024-01 예산 1500000원
```

#### 5-2. 예산 초과 시 경고 출력
목표 예산 1,000,000원 설정 상태에서 지출 1,230,000원 발생 시:
```bash
$ python3 -m budget_app summary --month 2024-01
총 수입: 3250000원
총 지출: 1230000원
잔액: 2020000원
예산: 1000000원 (사용률 123.0%) [경고: 예산 초과!]

지출 TOP 3
1) shopping 450000원
2) living 400000원
3) food 220000원
```
* **결과 입증**: 예산 데이터가 `budgets.jsonl`에 영구 보존되고, 사용률 100% 초과 시 `[경고: 예산 초과!]` 메시지가 활성화됨.

---

### 6. 카테고리 관리 (category add/list/remove) & 무결성 보호

#### 6-1. 기본 카테고리 목록 자동 시드 확인
```bash
$ python3 -m budget_app category list
- food
- transport
- living
- salary
- entertainment
- shopping
- medical
- etc
```

#### 6-2. 신규 카테고리 추가
```bash
$ python3 -m budget_app category add travel
[저장 완료] category=travel
```

#### 6-3. 기본 카테고리 삭제 차단 보호
```bash
$ python3 -m budget_app category remove food
[오류] 기본 카테고리 'food'는 삭제할 수 없습니다.
[힌트] 사용자가 직접 추가한 카테고리만 삭제 가능합니다.
```

#### 6-4. 사용 중인 카테고리 삭제 시 대체 카테고리 이전 정책
```bash
$ python3 -m budget_app category remove travel --replace-with food
[삭제 및 이전 완료] category=travel -> food
```
* **결과 입증**: 참조 무결성 보호와 함께 대체 카테고리 이전 마이그레이션 정책이 완벽히 작동함.

---

### 7. 거래 수정 (update) - 옵션 기반 부분 수정

```bash
$ python3 -m budget_app update --id TX-010013 --amount 30000 --memo "카페 음료 및 조각케이크 세트"
[수정 완료] id=TX-010013

$ python3 -m budget_app list --limit 1
TX-010013 | 2024-01-31 | expense | food | 30000 | 카페 음료 및 조각케이크 세트
```
* **결과 입증**: 금액과 메모가 원자적으로 갱신되었음을 재조회를 통해 확인.

---

### 8. 거래 삭제 (delete) - ID 기반 삭제 & 없는 ID 처리

#### 8-1. 정상 삭제
```bash
$ python3 -m budget_app delete --id TX-010013
[삭제 완료] id=TX-010013
```

#### 8-2. 존재하지 않는 ID 삭제 시도
```bash
$ python3 -m budget_app delete --id TX-NOTFOUND
[오류] ID 'TX-NOTFOUND'에 해당하는 거래를 찾을 수 없습니다.
[힌트] list 명령어로 올바른 거래 ID를 확인하세요.
$ echo $?
3
```
* **결과 입증**: 존재하지 않는 ID에 대해 `NotFoundError`와 함께 `exit code 3` 반환.

---

### 9. CSV 내보내기 (export) - 스키마 준수 및 건수 출력

```bash
$ python3 -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ head -n 4 export.csv
date,type,category,amount,memo,tags
2024-01-30,expense,transport,25000,야근 후 택시 귀가,"교통,야근"
2024-01-28,expense,food,55000,주말 가족 외식,"식비,외식"
2024-01-26,expense,shopping,265000,온라인 쇼핑몰 생필품 및 전자기기,"쇼핑,생활"
```
* **결과 입증**: UTF-8 헤더(`date,type,category,amount,memo,tags`)를 포함한 정합성 높은 CSV 생성 완료.

---

### 10. CSV 가져오기 (import) - 부분 임포트 & 스킵 상세 리포트

#### 10-1. 오류 행이 섞인 CSV 파일 생성
```csv
date,type,category,amount,memo,tags
2024-01-25,expense,food,8000,김밥,snack
2024-99-99,expense,food,5000,에러일자,error
2024-01-26,expense,food,-100,음수금액,error
```

#### 10-2. import 실행 및 결과
```bash
$ python3 -m budget_app import --from import_test.csv
[완료] imported=1, skipped=2
[스킵 상세 리포트]
  - 3행: 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
  - 4행: 금액은 양의 정수여야 합니다.
```
* **결과 입증**: 전체 실패 대신 유효한 1건은 즉시 등록하고, 오류가 발생한 2건은 행 번호와 구체적 사유를 상세히 리포트하는 Best-Effort 부분 임포트 정책 완벽 동작.
