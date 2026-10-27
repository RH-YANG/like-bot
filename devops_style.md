# DevOps Convention

FastAPI(back) + PostgreSQL 18(db) + React/Vite(front) + Playwright(worker)의 로컬 Docker 개발환경 규칙.

## 1. 파일과 환경변수

| 위치 | 역할 |
|---|---|
| `docker-compose.yml` | 로컬 실행 구성 |
| `back/`, `db/`, `front/`의 `Dockerfile` | 서비스별 이미지 |
| 루트 `.env` | 환경변수 단일 관리 |
| 루트 `.env.example` | 공유할 환경변수 목록 |
| 루트 `.dockerignore`, `.gitignore` | 빌드 제외·Git 제외 규칙 |

- 환경파일은 프로젝트 루트의 `.env` 하나로 통일한다. 서비스별 환경파일을 따로 두지 않는다.
- 실제 비밀값은 커밋하지 않고 `.env.example`만 공유한다.
- DB 인증 정보, 로그인 세션 암호화 키, VNC 비밀번호는 환경변수로 관리한다.
  포트·내부 호스트·네트워크 정책은 Compose에 직접 선언한다.
- Compose는 루트 `.env`를 자동으로 읽는다. 필요한 변수만 각 컨테이너의 `environment:`로 전달한다.
- 프런트에 노출하는 값은 공개 정보로 취급한다. 비밀번호와 암호화 키를 프런트에 전달하지 않는다.
- 변수 변경 시 `.env.example`, Compose 설정, 읽는 코드를 함께 갱신한다.
- 비즈니스 상수는 애플리케이션 코드·설정 파일에서 관리한다.
- Git 제외 규칙은 루트 `.gitignore`에 모아 작성한다.

## 2. 이미지 빌드

- 빌드 컨텍스트는 프로젝트 루트(`context: .`)로 통일한다.
  Dockerfile은 서비스 폴더에 두고 `COPY` 경로에 서비스명 접두어를 붙인다.
- `.dockerignore`는 루트 하나로 관리한다. 비밀값·캐시·의존성·빌드 산출물을 제외한다.
- back 패키지는 `requirements.txt`에서 `==`로 고정한다.
  front는 lockfile을 커밋하고 `npm ci`로 설치한다.
- 기반 이미지는 버전 태그를 명시한다.
- back의 `--reload`는 Compose의 실행 명령에 지정한다.
- front는 Vite를 `--host`로 실행한다. `/api` 요청은 Vite가 back으로 프록시한다.
- db는 PostgreSQL 18 공식 이미지에 `TZ=UTC`와 초기 스키마를 추가한다.
  사용자·DB 생성은 `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`에 위임한다.
- worker는 back과 같은 이미지를 사용하되 별도 명령으로 실행한다.

## 3. 서비스와 네트워크

- 프로젝트명은 `name: like-bot`, 컨테이너명은 `like-bot-{서비스}`로 한다.
- 네트워크는 `like-bot-net` 커스텀 bridge 하나를 사용한다.
  컨테이너 간 통신은 서비스명과 내부 포트를 사용한다.
- 호스트 공개 포트는 `127.0.0.1`에만 바인딩한다.

| 서비스 | 호스트 주소 | 소스 반영 |
|---|---|---|
| db | `127.0.0.1:5433` | 스키마 변경은 별도 적용 |
| back | `127.0.0.1:8001` | `./back:/app` 마운트와 `--reload` |
| front | `127.0.0.1:3001` | 소스·설정 파일 선별 마운트와 Vite |
| worker | `127.0.0.1:6080` | `./back:/app` 마운트, 코드 변경 후 재시작 |

- 준비 상태가 필요한 의존성은 `depends_on`의 `service_healthy`와 healthcheck로 연결한다.
  고정 시간 `sleep`으로 기동을 기다리지 않는다.
- DB healthcheck는 10초, back·worker는 30초 간격이다. 초기화 유예는 서비스별로 설정한다.
- `pg_isready`는 DB 연결 수락 여부, `/openapi.json`은 API 응답 여부를 확인한다.
  업무 기능 전체의 정상 여부는 별도 테스트로 확인한다.
- worker는 heartbeat로 실행 루프의 생존 여부를 확인한다.
- front는 `src/`, `public/`, `script/`, `index.html`, 루트 설정 파일을 선별 마운트한다.
  이미지의 `node_modules`를 가리지 않도록 하며, 새 설정 파일은 마운트 목록에 추가한다.
- Windows 파일 워칭은 back의 `WATCHFILES_FORCE_POLLING=true`, front의 `usePolling: true`를 사용한다.
- 패키지·lockfile·Dockerfile 변경 시 해당 이미지를 다시 빌드한다.
- 브라우저의 `/api/*`는 Vite가 `back:8000`으로 프록시하고 `/api` 접두어를 제거한다.
  프록시 주소는 Compose의 `API_URL`로 전달하며 `VITE_` 접두어를 붙이지 않는다.

## 4. 데이터와 브라우저

- DB 데이터는 named volume `db-data`를 `/var/lib/postgresql`에 마운트한다.
  PostgreSQL 18의 실제 데이터 경로는 `/var/lib/postgresql/18/docker`다.
- DB Dockerfile은 `db/schema.sql`을 `/docker-entrypoint-initdb.d/001-schema.sql`로 복사한다.
  빈 데이터 디렉터리의 최초 기동에서 자동 적용한다.
- 기존 DB 볼륨에는 이미지 재빌드·재기동만으로 스키마 변경이 반영되지 않는다.
  변경 적용과 스냅샷 동기화는 [DB 컨벤션](db/db_style.md)을 따른다.
- DB 백업은 `pg_dump`를 사용한다. 실행 중인 DB 데이터 디렉터리를 단순 복사하지 않는다.
- 시간 처리 기준은 UTC이며, DB 세션의 timezone도 UTC로 유지한다.
- Threads 로그인은 worker의 가상 화면에 연결하는 noVNC에서 직접 수행한다.
  VNC 비밀번호는 `.env`에서 관리하고 정확히 8자로 설정한다.
- 암호화한 로그인 상태는 `browser-session` named volume에 보관한다.
  암호화 키는 `.env`의 `SESSION_KEY`로 관리한다.
- 브라우저의 임시 프로필은 worker의 `/tmp` tmpfs에서 사용한다.
- `ENABLE_DESKTOP`은 기본 `true`로 두며 로그인 화면을 활성화한다. 브라우저 검증 등 화면이 필요 없는 실행에서는 `false`로 바꿀 수 있다.
- `docker compose down`은 named volume을 유지한다. `down -v`는 DB와 로그인 상태까지 삭제하므로 데이터 초기화가 필요한 경우에만 사용한다.

## 5. 실행

프로젝트 루트에서 실행한다.

```powershell
python back/util/init_env.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs -f back worker
docker compose restart worker
docker compose down
```

- 초기 환경 준비 스크립트는 기존 `.env`를 덮어쓰지 않는다.
- 이미지 변경이 없으면 `docker compose up -d`로 기동한다.
- `config`는 비밀값을 포함할 수 있으므로 문법 검증만 할 때는 `--quiet`를 사용한다.
