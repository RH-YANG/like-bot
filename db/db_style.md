# DB Convention

PostgreSQL 18의 로컬 스키마 설계·관리 컨벤션. Docker 컨테이너를 사용한다.

## 목차

1. [테이블 설계](#1-테이블-설계)
   - [PK 컬럼](#pk-컬럼) · [FK 컬럼](#fk-컬럼) · [복합 PK](#복합-pk)
   - [제약조건 네이밍](#제약조건-네이밍) · [UNIQUE / 인덱스 규칙](#unique--인덱스-규칙)
   - [공통 컬럼 규칙](#공통-컬럼-규칙) · [문서화](#문서화)
2. [디렉토리 구조](#2-디렉토리-구조) — 파일 배치, 컨테이너 구성표
3. [스키마 관리](#3-스키마-관리) — 소스 오브 트루스, schema.sql 스냅샷 동기화

---

## 1. 테이블 설계

### PK 컬럼
- 모든 테이블의 PK 컬럼명은 **`id`**
- `GENERATED ALWAYS AS IDENTITY` 사용 (시퀀스를 별도로 만들지 않는다)

```sql
CREATE TABLE member (
    id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email character varying NOT NULL,
    name  character varying
);
```

### FK 컬럼
- FK 컬럼명은 **`{참조 테이블명}_id`** 형식으로 작성한다 (`member_id`는 어디에 있든 `member.id`를 가리킨다)
- 컬럼명만 보고 참조 테이블을 바로 추론할 수 있어야 한다 (약어 사용 금지)

```sql
CREATE TABLE protein (
    id        integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id integer NOT NULL REFERENCES member(id),
    name      character varying
);
```

### 복합 PK
- 매핑/연결 테이블은 서러게이트 키 없이 자연 복합키 사용
```sql
CREATE TABLE my_protein (
    member_id  integer NOT NULL REFERENCES member(id),
    protein_id integer NOT NULL REFERENCES protein(id),
    PRIMARY KEY (member_id, protein_id)
);
```

### 제약조건 네이밍
- PK: `{table}_pk`
- FK: `{table}_fk` (같은 테이블에 FK가 여러 개면 `{table}_fk_1`, `{table}_fk_2` 순번 부여)
- UNIQUE: `{table}_{column}_uk` (복합이면 컬럼명을 `_`로 연결)
- INDEX: `{table}_{column}_idx`

### UNIQUE / 인덱스 규칙
- 외부에 노출되어 조회 키로 쓰이는 컬럼(`public_uuid` 등)은 **UNIQUE 제약이 필수**다. 무결성과 인덱스를 동시에 확보한다.
- 반복 조회 경로의 컬럼(FK, 토큰 해시 등)에는 인덱스를 만든다. PostgreSQL은 FK 컬럼에 인덱스를 자동 생성하지 않는다.

### 공통 컬럼 규칙
- boolean 컬럼은 `is_` 접두어 (`is_public`, `is_activate`)
- 가변 문자열은 길이 제한 없는 `character varying`으로 통일
- 생성/수정 시각은 `created_at` / `updated_at`, 타입은 `timestamp with time zone DEFAULT CURRENT_TIMESTAMP`
- datetime 값은 **UTC로 저장**한다. 표현 변환은 애플리케이션 레이어에서 담당한다
- 생성/수정 주체를 남길 때는 `created_by` / `modified_by` (둘 다 `member.id`를 참조하는 FK, 컬럼명은 `member_id` 규칙 예외로 의미를 명확히 한다)
- 애플리케이션 모델(back의 `schema.py`)에서 필수인 컬럼은 DB도 `NOT NULL`로 선언한다. 두 레이어의 nullable 판단이 어긋나지 않게 유지한다
- 토큰 등 민감값 컬럼은 원문 대신 SHA-256 해시를 저장한다 (DB 유출 시 원문 보호)

### 문서화
- **테이블 단위**: `COMMENT ON TABLE`로 테이블의 목적을 남긴다 (유지)
  ```sql
  COMMENT ON TABLE member IS '플랫폼의 회원 데이터를 저장하는 테이블.';
  ```
- **컬럼 단위**: `COMMENT ON COLUMN`은 사용하지 않는다. 대신 CREATE TABLE 내부에 인라인 SQL 주석(`--`)으로 남긴다
  ```sql
  CREATE TABLE member (
      id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      email character varying NOT NULL,  -- 로그인시 사용되는 이메일 계정
      pwd   character varying NOT NULL,  -- 로그인 비밀번호
      name  character varying            -- 사용자 이름
  );
  ```
  - 이유: 컬럼당 8줄짜리 `COMMENT ON COLUMN` 블록이 schema.sql을 비대하게 만들고 git diff에서 노이즈를 키운다. 인라인 주석은 짧고 git diff에서도 바로 보인다.
- **주석-코드 동기화**: enum성 컬럼의 값 목록 주석(`-- terms_platform | ...`)은 실제 코드(front/back)가 쓰는 값과 일치시키고, 값이 바뀌면 같은 커밋에서 갱신한다
  - 이유: 인라인 주석이 곧 데이터 사전 — 어긋나면 잘못된 검증 로직의 근거가 된다

---

## 2. 디렉토리 구조

```
db/
├── Dockerfile              # PostgreSQL 이미지 빌드 정의
├── db_style.md             # DB 개발 컨벤션 (이 파일)
└── schema.sql              # 현재 DB 스키마 스냅샷 (git으로 이력 추적)
```

### 컨테이너 구성

`docker compose`로 컨테이너를 띄운다. 주요 설정:

| 항목 | 값 |
|---|---|
| 컨테이너명 | `like-bot-db` (compose 서비스명은 `db` — 내부 네트워크 호스트명으로 사용) |
| 이미지 | `./db/Dockerfile` 빌드 (`postgres:18`) |
| 포트 | 호스트 `127.0.0.1:5433` → 컨테이너 `5432` |
| 데이터 볼륨 | named volume `db-data` → `/var/lib/postgresql` (PGDATA: `/var/lib/postgresql/18/docker`) |
| 타임존 | UTC (Dockerfile `ENV TZ=UTC` — 초기화 시점에 적용) |
| 네트워크 | `like-bot-net` |
| Healthcheck | `pg_isready -U ${DB_USER} -d ${DB_NAME}` (10초 간격, 최대 5회, 초기화 유예 30초) |

환경변수(`DB_USER`, `DB_PWD`, `DB_NAME`)는 루트의 `.env`에서 관리한다.

---

## 3. 스키마 관리

실제 소스 오브 트루스는 **컨테이너 안의 DB**다. `schema.sql`은 현재 DB 스키마를 한눈에 보기 위한 스냅샷 파일이며, 변경 이력 추적은 git history로 한다.

### schema.sql 갱신

스키마 변경은 로컬 DB와 스냅샷에 함께 반영한다.

1. `like-bot-db` 컨테이너에서 변경 DDL을 적용한다 (소스 오브 트루스).
   ```powershell
   docker compose exec db psql -U like_bot -d like_bot
   ```
   사용자·DB 이름은 루트 `.env`의 값에 맞춘다. 관련 DDL은 가능한 한 하나의 트랜잭션으로 처리한다.
2. `schema.sql`에 같은 스키마를 이 문서의 스타일(정렬·인라인 주석·제약조건 네이밍)대로 수기 반영한다.
3. back의 `schema.py`, DTO, DAO와 관련 테스트를 함께 갱신한다.

- `schema.sql`은 빈 DB 볼륨의 최초 초기화에도 사용한다. 기존 DB에는 재빌드·재기동만으로 적용되지 않는다.
- 별도 변경 SQL 파일을 누적하지 않으며 스키마 변경 이력은 Git에서 확인한다.
- `pg_dump`로 `schema.sql`을 덮어쓰지 않는다. 인라인 주석이 사라져 데이터 사전이 소실된다.
- DB 백업은 `pg_dump`를 사용한다. 실행 중인 데이터 디렉터리를 단순 복사하지 않는다.
- `docker compose down`은 데이터를 유지한다. `down -v`는 DB와 브라우저 로그인 상태를 모두 삭제하므로 전체 초기화가 필요할 때만 사용한다.
