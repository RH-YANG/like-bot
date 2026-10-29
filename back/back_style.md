# Backend Coding Style Guide

FastAPI + PostgreSQL(psycopg2) 백엔드 개발 컨벤션.

## 1. 구조와 레이어 책임

| 위치 | 역할 |
|---|---|
| `api/*_api.py` | 라우팅, 요청·응답 변환, 주요 처리 흐름 조합 |
| `service/*_service.py` | 비즈니스 로직, 검증, 에러 처리 |
| `util/` | 공통 기술 처리와 개발 보조 코드 |
| `util/client/` | 외부 서비스 인증·API 호출·서명 검증·응답 파싱 |
| `util/handler/` | 공통 예외 처리와 시스템 오류 로그 기록 |
| `util/test/` | 서비스·DB·외부 연동 회귀 테스트 |
| `database/dao/*_dao.py` | SQL 실행과 조회 결과 매핑 |
| `database/schema.py` | DB에 직접 구현된 테이블의 모델 |
| `database/schema_enum.py` | 테이블 enum성 컬럼 중 분기·상태 전이에 쓰는 값 목록(`StrEnum`) |
| `database/dto.py` | API 요청·응답 모델 |
| `database/dbms_control.py` | DB 커넥션·커서 주입과 반환 |
| `job/` | worker 실행 루프(`run_worker.py`)와 작업 처리(`*_job.py`) |
| `llm/`, `config/` | LLM 구현, 주제별 조정값 |
| `env.py`, `main.py` | 환경변수 로드, 앱 초기화와 라우터 등록 |

- 기본 호출 방향은 `api → service → dao`이며 역방향 호출을 금지한다.
- API는 Job 체인 진입 함수를 호출할 수 있다. Job 구현도 DB 접근은 Service를 거친다.
- API에서 DAO를 직접 호출하지 않는다. 패키지 폴더에 `__init__.py`를 두지 않는다.
- API 파일과 라우터는 DB 테이블에 근거한 도메인 단위로 만든다. 테이블명과 꼭 같을 필요는 없고 여러 테이블을 묶을 수 있다
  (`targeting_api`는 `targeting_set`·`target_keyword`를 다룬다). 테이블 근거가 없는 독립 도메인(`platform_api` 등)은 만들지 않는다.
  설정값·집계처럼 테이블이 없는 기능은 근거가 되는 도메인에 둔다(예: 좋아요 사용량 → `GET /post/like-usage`).
  Service도 같은 도메인 또는 그 묶음 단위로 둔다(`targeting_api` → `targeting_service`).

### API

- 단순 요청은 Service에 위임한다. 복합 요청은 주요 단계와 분기를 API에서 드러낸다.
- Service 결과에 따른 분기는 허용한다. 도메인 상태 판단·검증·에러 처리는 Service에 둔다.
- SQL, 암호화, 외부 API 호출, 커넥션 전달, `commit`·`rollback`을 API에 작성하지 않는다.
- 원자적으로 처리해야 하는 작업은 하나의 진입 함수로 호출한다. 트랜잭션을 쪼개면서까지
  내부 단계를 API에 노출하지 않는다.
- 함수 호출 결과는 의미 있는 변수에 먼저 할당하며, 응답 모델 생성자 안에 함수 호출을 중첩하지 않는다.
- 최종 응답 모델도 반환 대상이 드러나는 변수로 만든 뒤 반환한다.

```python
rooms = chat_room_service.select_rooms(member)

chat_room_list = ChatRoomListResponse(rooms=rooms)

return chat_room_list
```

### Service와 DAO

- DAO는 테이블당 하나, 파일명은 정확히 `{table}_dao.py`. 담당 테이블만 변경하며 조회용 JOIN·서브쿼리는 허용한다.
- Service는 `{domain}_service.py`. 응집성과 기존 구조에 따라 관련 테이블을 통합하며, 테이블별로 불필요하게 분리·개명하지 않는다.
  예: `log_service`는 `log_event`·`log_error`를 담당할 수 있다.
- 여러 테이블의 변경은 Service에서 DAO·Service를 조합해 한 트랜잭션으로 처리한다.
- Service는 도메인 조건과 실패 원인을 판단하고, DAO는 SQL 실행만 담당한다.
- DAO의 첫 인자는 `cur`이다. 커넥션 생성·반환과 `commit`·`rollback`은 하지 않는다.
- 테이블 단건 조회는 해당 테이블 모델 또는 `None`, 목록 조회는 리스트(없으면 `[]`)를 반환한다.
  조인·복합 집계 결과가 테이블 모델과 다르면 dict 또는 dict 목록으로 반환하고 Service에서 기존 DTO로 변환한다.
  단순 집계는 숫자를 반환한다.
- 단건 조회의 부재는 Service에서 `is None`으로 확인한다.

### Util과 외부 클라이언트

- Service는 내부 도메인을 위한 레이어이다. 외부 서비스의 인증·API 호출·서명 검증·응답 파싱은 `util/client/`에 둔다.
- 외부 클라이언트 파일은 `{외부 서비스명}.py`로 명명한다.
- `util/handler/`에는 각종 핸들러를 위치시킨다.
- `util/test/`에는 각종 테스트 파일을 위치시킨다. `back` 폴더에서 `python -m pytest util/test`로 실행한다.
- 브라우저 자동화는 `util/client/{플랫폼}.py`에 둔다. 화면 선택자·라벨은 파일 상단 상수로 모아 화면이 바뀌면 그곳만 고친다.
- 계정 상태 예외(로그인 풀림·본인 인증·활동 제한)는 `util/handler/platform_exception.py`에 두고, 감지하면 실행을 즉시 멈춘다.

### Worker

- worker는 DB의 `run`을 큐로 쓴다. `pending` 실행을 `FOR UPDATE SKIP LOCKED`로 하나씩 가져와 `running`으로 바꾼다.
- 실행 조건(목표 개수·키워드·플랫폼 설정)은 실행 중에 `targeting_set`을 다시 읽지 않고 `run.targeting_snapshot`에서 읽는다.
- 실행 루프는 주기적으로 `run.heartbeat_at`을 갱신하고 그때 중지 요청(`stopping`)을 확인한다.
  heartbeat가 끊긴 실행은 worker 시작 시와 실행 생성·목록 조회 시 `interrupted`로 정리한다.
- 좋아요는 결과를 기록할 행을 먼저 저장한 뒤 누르고, 결과에 따라 상태를 바꾼다.


## 2. DB 접근과 트랜잭션

### 함수별 책임

| 함수 종류 | DB 인자와 처리 방식 |
|---|---|
| DB 진입 함수 | `@connect_db`를 붙이고 `(conn, cur, ...)`로 시작한다. 변경 성공 시 커밋한다. |
| 트랜잭션 내부 함수 | 데코레이터 없이 필요한 `conn, cur` 또는 `cur`를 받는다. 직접 커밋하지 않는다. |
| DB 없는 함수 | DB 인자와 데코레이터를 사용하지 않는다. |

- 커넥션 풀과 커서의 생성·반환은 데코레이터가 담당한다. 조회에는 `DictCursor`를 사용한다.
- 같은 작업에서 함께 성공해야 하는 변경은 하나의 진입 함수에서 처리하고 마지막에 한 번
  커밋한다. 내부 함수에서 다른 `@connect_db` 함수를 호출해 트랜잭션을 분리하지 않는다.
- 부모·자식 생성, 상태 변경과 이력 저장, JobSession·Job 등록은 같은 트랜잭션에 묶는다.
- 변경 전에 소유권과 현재 상태를 같은 트랜잭션에서 다시 확인한다. 선행 조회 결과만 믿지 않는다.
- 동시 변경과 경쟁하는 조회에는 필요에 따라 행 잠금을 사용하고, 잠금 순서를 일관되게 유지한다.
- `Depends()`에 직접 사용하는 함수에는 `@connect_db`를 붙이지 않는다.
  일반 시그니처의 의존성 함수에서 별도 DB 진입 함수를 호출한다.

```python
@connect_db
def create_potion(conn, cur, potion, auto_generate_shadow, member):
    # → 포션과 선택적 그림자 생성 체인을 함께 저장한다
    # 1. 포션 저장
    potion_id = potion_service.insert(conn, cur, potion)

    # 2. 요청된 그림자 체인 등록
    shadow_id = None
    if auto_generate_shadow:
        shadow_id = create_shadow_chain(conn, cur, potion_id, member)

    # 3. 전체 변경 확정
    conn.commit()

    return potion_id, shadow_id
```

### 에러와 민감값

- 서비스 HTTP 오류는 `HTTPException`과 `status` 상수로 표현한다.
- 입력 검증 실패는 400, 조회 대상 부재는 404로 처리한다. 인증·권한·상태 충돌은 원인에 맞게 구분한다.
- 실행됐어야 할 DML의 실패는 `db_fail_routine(conn)`으로 롤백하고 503을 반환한다.
  정상적인 조회 부재나 이미 교체된 Job 회차를 DML 실패로 취급하지 않는다.
- 민감값의 평문 저장은 금지한다. 비교만 필요한 값은 SHA-256 해시로 저장·비교하고,
  재사용을 위해 복호화가 필요한 값은 인증 암호화로 보관한다.

## 3. 모델과 SQL

### Pydantic 모델

- DB에 직접 구현된 테이블의 모델만 `database/schema.py`에 둔다.
  API 요청·응답 모델은 `database/dto.py`에 둔다.
  enum성 컬럼 중 코드에서 분기·상태 전이에 쓰는 값은 `database/schema_enum.py`에 `StrEnum`으로 선언한다.
  멤버명은 UPPER_SNAKE_CASE, 값은 소문자 snake_case로 쓰고, 코드에서는 문자열 대신 멤버(`RunStatus.RUNNING`)로 비교·대입한다.
  값이 적고 분기에 거의 쓰지 않는 컬럼은 모델에 직접 `Literal['a', 'b']`로 선언한다.
  어느 방식이든 값은 `schema.sql`의 인라인 주석과 일치시킨다.
  조인·집계 조회만을 위한 중간 모델을 `schema.py`에 추가하지 않는다. 기존 응답 모델을 먼저 재사용한다.
  외부 연동 전용 모델은 해당 `util/client/*.py`에 모으며, Service에서는 모델 선언을 지양한다.
  외부 연동 모델의 선언 위치와 관계없이 도메인 검증·판단은 Service에서 수행한다.
- 내부 모델의 NOT NULL 컬럼은 필수 타입, nullable 컬럼은 `Optional[T] = None`으로 선언한다.
  DB가 자동 생성하는 필드는 NOT NULL이어도 `Optional[T] = None`으로 둔다.
- 요청의 필수 필드는 필수 타입으로 선언한다. 선택 필드는 `Optional[T] = None`을 기본으로 하며,
  명시적인 기본값이 있는 항목은 해당 타입과 기본값을 선언한다.
- 모든 API 요청·응답 모델은 `ApiModel`을 상속한다. Python 필드는 snake_case,
  JSON 키는 `to_camel` alias로 통일한다. Python 이름으로도 생성할 수 있게 설정한다.
- 응답에는 클라이언트에 공개할 필드만 둔다. 내부 모델에서 DTO로 변환할 때는
  `from_attributes=True`와 `model_validate()`를 활용할 수 있다.

### SQL

- 키워드는 대문자, 컬럼은 세로로 나열하고 쉼표는 줄 앞에 둔다.
  `FROM`, `WHERE` 등 주요 절의 키워드 끝을 `SELECT`에 맞춰 정렬한다.
- 모델을 받으면 named placeholder와 `model_dump()`를, 개별 인자를 받으면 `%s`와 tuple을 사용한다.
  모델 필드를 다시 tuple로 풀거나 개별 인자를 임시 dict로 감싸지 않는다.
- 값은 문자열 보간하지 않는다. 동적 컬럼명 등 식별자는 허용 목록으로 검증한 뒤 삽입한다.
- 상태 전이 UPDATE의 `WHERE`에는 기대하는 현재 상태를 포함한다.

```python
query = '''
    UPDATE job
       SET status = 'done'
         , finished_at = CURRENT_TIMESTAMP
     WHERE id = %s
       AND status = 'processing'
'''
cur.execute(query, (job_id,))
```

## 4. 이름과 코드 형식

### 이름과 임포트

- 폴더명·파일명·모델명·클래스명·함수명 등 모든 이름은 단수형을 기본으로 한다.
- 복수형 예외는 변수명에만 적용한다. 단수 변수가 이미 선언되어 있고, 해당 인스턴스들의
  리스트·컬렉션을 구분해야 할 때 복수형을 사용한다(`member`와 `members`).
  리스트·컬렉션이라는 이유만으로 복수형을 사용하지 않는다.
- 파일·함수·변수는 snake_case, 클래스는 PascalCase로 작성한다. 함수명에는 동작 동사를 포함한다.
- API·Service·DAO 파일은 각각 `*_api.py`, `*_service.py`, `*_dao.py`로 이름 짓는다.
- 내부 모델은 도메인명, 요청·응답은 `{Action}Request/Response`로 이름 짓는다.
  도메인 간 이름 충돌이 있을 때만 도메인명을 앞에 붙인다.
- DB 식별자는 `member_id`, `chat_room_id`처럼 의미가 드러나는 `_id` 이름을 사용한다.
- 라우터는 `APIRouter(prefix="/{domain}", tags=["{domain}"])`로 선언한다.
- Pydantic·도메인 객체는 함수 인자 안에서 생성하지 않고 변수로 만든 뒤 전달한다.
- 임포트는 표준 라이브러리·서드파티 다음에 빈 줄 1개를 두고 로컬 모듈을 배치한다.
  로컬 레이어 임포트의 상대 순서는 `service → dao → schema → dto`로 한다.
- Service·DAO는 모듈 전체를 임포트하고, 모델은 정의 파일에서 필요한 클래스를 임포트한다.
  `as`는 모듈명 축약(`import service.auth_service as auth_service`)이나 이름 충돌 해소에 사용한다.
- import문은 길이와 관계없이 한 줄로 작성한다.

### 반환값

- 값을 반환할 때는 반환 대상의 의미가 드러나는 이름으로 변수를 선언·할당하고, 그 변수를 `return`한다.
  `result`, `data`처럼 대상이 불분명한 이름보다 `job_session_id`, `chat_room_list`처럼 구체적인 이름을 사용한다.
- 함수 호출·객체 생성·연산·삼항 조건식을 반환문에 직접 작성하지 않는다.
  조건에 따른 값 선택은 별도 분기로 처리하고, 최종 반환 변수에 할당한다.
- 이 규칙은 모든 레이어의 함수·메서드·`@property`에 공통으로 적용하며 API 응답 모델도 예외로 두지 않는다.

### 빈 줄과 시그니처

| 빈 줄 수 | 적용 대상 |
|---|---|
| 0 | 같은 의미 단위, 가드절·이른 반환 |
| 1 | 함수 내 논리 단계, 최종 `return` 앞 |
| 2 | 길고 독립적인 논리 블록 사이 |
| 3 | 임포트 영역과 본문 사이, 독립 함수·클래스·엔드포인트 사이 |

- API 함수 시그니처는 80자, Service·DAO 함수 시그니처는 120자를 기준으로 줄바꿈한다.
- 기준을 넘거나 파라미터가 복잡하면 한 줄에 하나씩 4칸 들여쓰고 마지막에도 쉼표를 붙인다.
  닫는 `)`와 반환 타입은 같은 줄에 둔다.

### 주석

- API 라우트 본문의 첫 줄에는 기능과 호출자가 알아야 할 정보를 간결한 docstring으로 작성한다.
- Service 함수의 첫 줄에는 `# →`로 기능을 설명한다.
- `schema.py`의 테이블 모델은 클래스 첫 줄에 `'''` 여러 줄 docstring으로 테이블명과 목적·제약을 적는다.
- 파일 역할 설명은 임포트 뒤에 `# ========== 설명 ==========` 형식으로 작성한다.
- 복합 API와 서로 다른 처리를 조합하는 긴 Service 함수에는 주요 단계별 번호 주석을 붙인다.
  짧은 단일 조회·변환·상태 변경에는 번호 주석을 붙이지 않는다.
- 인라인 주석은 코드에서 공백 4칸 이상 띄우고 같은 블록에서는 시작 위치를 맞춘다.

## 5. 시간·설정·앱 초기화

- 저장·비교·계산에는 timezone-aware UTC datetime을 사용한다. 현재 시각은
  `datetime.now(timezone.utc)`로 얻고 DB 세션의 timezone도 UTC로 유지한다.
- 사용자 표시와 LLM 프롬프트·생성 로그의 시각 표기는 필요에 따라 `Asia/Seoul`로 변환한다.
- 환경변수는 `env.py`에서만 읽고 이름·기본값·타입 변환을 관리한다. 호출부는 `import env`를 사용한다.
- 한 번 정해두고 코드로 관리하는 조정값은 `config/{주제}.py`에 둔다(`config/llm.py`, `config/platform.py`).
  페이지 크기 같은 비즈니스 상수는 해당 도메인에 둔다.
  API 키·비밀번호·암호화 키는 환경변수로 관리한다.
- `main.py`는 앱 초기화·라이프사이클·공통 예외 처리·라우터 등록을 담당한다.
- 현재 프런트 프록시를 통한 same-origin 통신 구조에서는 CORS 미들웨어를 추가하지 않는다.
