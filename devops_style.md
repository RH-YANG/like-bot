# DevOps Convention

FastAPI(back) + PostgreSQL 18(db) + React/Vite(front)의 개발·운영 컨테이너 구성 규칙.

## 1. 파일과 환경변수

| 위치 | 역할 |
|---|---|
| `docker-compose.yml` | 개발 환경 |
| `docker-compose.prod.yml` | 운영 환경 |
| `back/`, `db/`, `front/`의 `Dockerfile` | 서비스별 개발 이미지, back·db는 운영에서도 사용 |
| `front/Dockerfile.prod` | 운영 프런트 빌드와 Nginx 이미지 |
| `Caddyfile` | 운영 HTTPS 진입점 |
| `cloud-init.yml` | Azure VM 최초 초기화 |
| 루트 `.env` | 개발·운영 환경변수 단일 관리 |
| 루트 `.env.example` | 공유할 환경변수 목록 |
| 루트 `.dockerignore`, `.gitignore` | 빌드 제외·Git 제외 규칙 |

- 환경파일은 프로젝트 루트의 `.env` 하나로 통일한다. 서비스별·개발/운영별 환경파일을 따로 두지 않는다.
- 실제 비밀값은 커밋하지 않고 `.env.example`만 공유한다.
- 비밀값·외부 서비스 식별자·환경별 기능 토글은 환경변수로 관리한다.
  포트·내부 호스트·네트워크 정책은 개발/운영 Compose에 직접 선언한다.
- 개발·운영 Compose 모두 루트 `.env`를 자동으로 읽는다. 환경파일을 별도로 지정하지 않는다.
- 필요한 변수만 컨테이너의 `environment:` 또는 프런트의 `build.args`로 전달한다.
  프런트 빌드에 전달하는 값은 브라우저에 공개되는 것으로 취급한다.
- 변수 변경 시 `.env.example`, 해당 Compose 설정, 읽는 코드를 같은 커밋에서 갱신한다.
- 비즈니스 상수와 LLM 조정값은 애플리케이션 코드·설정 파일에서 관리한다.
- Git 제외 규칙은 루트 `.gitignore`에 서비스·네이티브 프로젝트 경로까지 모아 작성한다.

## 2. 이미지 빌드

- 빌드 컨텍스트는 프로젝트 루트(`context: .`)로 통일한다.
  Dockerfile은 서비스 폴더에 두고 `COPY` 경로에 서비스명 접두어를 붙인다.
- `.dockerignore`는 루트 하나로 관리한다. 비밀값·캐시·의존성·빌드 산출물을 제외한다.
- back 패키지는 `requirements.txt`에서 `==`로 고정한다.
  front는 lockfile을 커밋하고 `npm ci`로 설치한다.
- 기반 이미지는 버전 태그를 명시한다. 태그 지정은 이미지 내용의 완전한 고정이 아니며,
  동일 이미지 재현이 필요한 배포에서는 digest를 고정한다.
- back의 기본 실행에는 `--reload`를 넣지 않는다. 개발 Compose에서만 덮어쓴다.
- 개발 front의 Vite는 `--host`로 실행한다. 운영 front는 정적 빌드를 Nginx로 제공한다.
- 개발·운영 db는 PostgreSQL 18 공식 이미지에 `TZ=UTC`와 초기 스키마를 추가한다.
  사용자·DB 생성은 `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`에 위임한다.

## 3. 개발·운영 구성

### 공통

- 프로젝트명은 `name: tmx`, 컨테이너명은 `tmx-{서비스}`로 한다.
- 컨테이너 통신은 커스텀 bridge 네트워크에서 서비스명과 내부 포트를 사용한다.
- 준비 상태가 필요한 의존성은 `depends_on`의 `service_healthy`와 healthcheck로 연결한다.
  고정 시간 `sleep`으로 기동을 기다리지 않는다.
- healthcheck의 초기화 유예와 주기는 서비스별로 설정한다.
  현재 DB는 10초, back·운영 front는 30초 간격이다.
- DB의 `pg_isready`는 서버가 연결을 수락하는지 확인한다. 인증·테이블·쿼리 성공까지
  보장하지 않는다. back의 `/openapi.json` 검사도 업무 기능 전체의 정상 여부를 보장하지 않는다.

### 개발

| 서비스 | 호스트 포트 | 소스 반영 |
|---|---|---|
| db | 5432 | 스키마 변경은 별도 적용 |
| back | 8000 | `./back:/app` 마운트와 `--reload` |
| front | 3000 | 소스·설정 파일 선별 마운트와 Vite |

- front는 `src/`, `public/`, `index.html`, 루트 설정 파일만 마운트한다.
  이미지의 `node_modules`를 가리지 않도록 하며, 새 설정 파일은 마운트 목록에 추가한다.
- Windows 파일 워칭은 back의 `WATCHFILES_FORCE_POLLING=true`, front의 `usePolling: true`를 사용한다.
- 패키지·lockfile·Dockerfile 변경 시 해당 이미지를 다시 빌드한다.
- 브라우저의 `/api/*`는 Vite가 `back:8000`으로 프록시하고 `/api` 접두어를 제거한다.
  프록시 주소는 Compose의 `API_URL`로 전달하며 `VITE_` 접두어를 붙이지 않는다.

### 운영

| 서비스 | 접근 경로 |
|---|---|
| caddy | 호스트 80·443 공개, HTTPS 처리와 HTTP 리다이렉트 |
| front | Caddy → `front:80`, Nginx 정적 파일과 `/api` 프록시 |
| back | Nginx → `back:8000`, 호스트 포트 미공개 |
| db | back → `db:5432`, 호스트에서는 `127.0.0.1:5432`로만 접근 |

- 운영은 소스 마운트와 개발 서버 없이 이미지에 포함된 코드를 실행한다.
- 네트워크는 `tmx-edge`와 `tmx-data`로 분리하고, DB는 추가로 `tmx-db-access`에 연결한다.
- Nginx는 `/api`를 제거해 back에 전달한다. Caddy가 전달한 실제 클라이언트 주소를
  사용하며, 프록시 헤더 신뢰 설정은 이 통신 경로에 맞춰 유지한다.
- 운영 서비스는 `restart: unless-stopped`를 사용한다.
- 초대 로그인 기본값은 `false`로 유지한다. 현재 Compose는 환경변수 재정의를 허용하므로
  배포 시 값을 확인하고 back 런타임과 front 빌드의 설정을 일치시킨다.

## 4. 데이터와 초기화

- 개발·운영 DB 데이터는 named volume `db-data`를 `/var/lib/postgresql`에 마운트한다.
  PostgreSQL 18의 실제 데이터 경로는 `/var/lib/postgresql/18/docker`다.
- 개발 업로드는 `_dev/upload`, 운영 업로드는 비공개 Azure Blob 컨테이너에 보관한다.
  Caddy의 인증서·상태는 `caddy-data`, `caddy-config` 볼륨에 보관한다.
- DB Dockerfile은 `db/schema.sql`을 `/docker-entrypoint-initdb.d/001-schema.sql`로 복사한다.
  빈 데이터 디렉터리의 최초 기동에서 자동 적용되므로 초기 스키마를 수동으로 다시 적용하지 않는다.
- 기존 DB 볼륨에는 이미지 재빌드·재기동만으로 스키마 변경이 반영되지 않는다.
  이후 변경 적용과 스냅샷 동기화는 [DB 컨벤션](db/db_style.md)을 따른다.
- DB 백업은 `pg_dump`를 사용하고 업로드 파일도 별도로 백업한다.
  실행 중인 DB 데이터 디렉터리를 단순 복사해 백업하지 않는다.
- `docker compose down`은 named volume을 유지한다. 운영 데이터가 있는 환경에서는 `down -v`를 사용하지 않는다.
- 시간 처리 기준은 UTC이며, VM·DB 설정과 실제 DB 세션의 timezone을 함께 확인한다.

## 5. 실행과 Azure 초기화

명령은 프로젝트 루트에서 실행한다. 환경파일은 `.env`로 통일하고 개발·운영은 Compose 파일로 구분한다.

```bash
# 개발: 빌드·기동, 상태, 로그, 종료
docker compose up -d --build
docker compose ps
docker compose logs -f back
docker compose down

# 운영: 설정 검증과 빌드·기동
docker compose -f docker-compose.prod.yml config --quiet
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

- 이미지 변경이 없으면 `up -d`, 로그·종료는 같은 운영 옵션에 `logs -f`·`down`을 사용한다.
- 값까지 출력하는 `config`에는 비밀값이 포함될 수 있다. 검증만 할 때는 `--quiet`를 사용한다.
- cloud-init은 OS·Docker·Azure CLI 설치, 운영 사용자 설정과 디렉터리 준비를 담당한다.
  현재 파일은 키 조회 스크립트를 생성하지만 자동 실행·clone·환경파일 배치·배포는 하지 않는다.
- SSH 사용자·공개 키·Managed Identity·NSG는 Azure VM 설정에서 관리한다.
- cloud-init을 수정할 때는 `#cloud-config`를 첫 줄에 두고 문법을 검증한다.
  비밀값을 파일·로그에 넣지 않고, 재실행 가능한 초기화 명령을 작성한다.
