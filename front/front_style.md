# 프론트엔드 개발 컨벤션

React 18 · TypeScript · Vite · React Router v6 · Axios · Zustand · CSS Modules

## 파일 배치

| 경로 | 역할 |
|---|---|
| `src/api/` | 공통 client를 사용하는 API 호출 함수 |
| `src/component/` | 여러 페이지에서 재사용하는 컴포넌트 |
| `src/page/` | 라우트별 페이지와 전용 컴포넌트·훅 |
| `src/hook/` | 여러 곳에서 사용하는 훅. 도메인별로 분리하며 UI 훅은 `ui/`에 배치 |
| `src/store/` | 도메인별 Zustand 전역 상태 |
| `src/type/` | 여러 모듈이 공유하는 도메인 타입 |
| `src/util/` | React에 의존하지 않는 공통 로직 |
| `src/config/` | 설정과 고정 데이터 |
| `src/asset/` | 이미지·폰트 등 정적 리소스 |
| `native-asset/` | Android·iOS 앱 아이콘 원본 |

- 한 기능에서만 쓰는 컴포넌트·훅·타입은 해당 기능 폴더에 둔다. 실제로 공유할 때 공통 폴더로 옮긴다.
- 기능 폴더 루트에는 컨테이너, CSS Module, 전용 훅을 둔다. 파일이 많아지면 `thread/`, `input/`처럼 역할별로 나눈다.
- 폴더명은 담긴 구성원의 역할을 나타내고, 불필요한 중첩과 `thread/Thread` 같은 이름 반복은 피한다.

## 이름

| 대상 | 형식·예시 |
|---|---|
| 컴포넌트·페이지 | PascalCase. 파일명과 대표 컴포넌트명을 일치시킨다: `Header.tsx` |
| CSS Module | 컴포넌트명과 일치: `Header.module.css` |
| 훅 | `use{Feature}.ts`. 역할 구분이 필요할 때만 접미어 추가: `useIntroSequence.ts` |
| API·스토어·타입 | `{domain}Api.ts`, `{domain}Store.ts`, `{domain}Type.ts` |
| 폴더·라우트 | 소문자 kebab-case: `make-potion/`, `/my-room` |
| 이미지 | snake_case: `my_room_clouds.webp` |

- 일반 변수·함수·CSS 클래스는 camelCase, 상수는 UPPER_SNAKE_CASE를 사용한다.
- boolean은 `is`, 이벤트 핸들러는 `handle`, state setter는 `set`, 토글 함수는 `toggle` 접두어를 사용한다.
- 폴더명·파일명·모델명·클래스명·함수명 등 모든 이름은 단수형을 기본으로 한다.
- 복수형 예외는 변수명에만 적용한다. 단수 변수가 이미 선언되어 있고, 해당 인스턴스들의
  리스트·컬렉션을 구분해야 할 때만 복수형을 사용한다(`member`와 `members`).
  리스트·컬렉션이라는 이유만으로 복수형을 사용하지 않는다.
- `Controller`, `Manager`처럼 역할이 모호한 훅 접미어는 피한다.

## 컴포넌트

- 내부 순서: `store → state → hook → handler → effect → return`. 필요한 섹션만 `// --- 섹션명`으로 구분한다.
- `export default ComponentName`은 파일 하단에 단독으로 작성한다.
- props·state에 의존하지 않는 상수는 컴포넌트 밖에 둔다.
- 렌더 중 계산할 수 있는 값은 별도 state로 저장하지 않는다.
- 팝업·새 창은 클릭 핸들러에서 지연 없이 연다. 연출용 지연 시간은 이름 있는 상수로 선언한다.

## API와 훅

- API 함수는 `api/client.ts`의 공통 인스턴스로만 호출하며 인증 헤더는 client에 맡긴다.
- API 파일의 도메인은 백엔드 엔드포인트를 따른다: `/member/consent` → `memberApi.ts`.
- API 함수는 React·상태 관리에 의존하지 않으며 응답을 가공하지 않는다. 응답 타입은 제네릭으로 지정한다: `client.post<LoginResponse>(...)`.
- API 소비 훅은 API 함수를 통해 요청하고 `{ data, isLoading, error, ...handlers }` 형태로 반환한다.
- 오류는 `ApiError`로 관리한다. 사용자용 `message`와 응답 `status`를 담고, 오류 초기화용 `clearError`를 제공한다.
- 제출 중 중복 호출을 막고 성공 여부나 결과를 반환한다. 내비게이션은 페이지에서 결정한다.
- 타이머·이벤트 리스너·이미지 로드 핸들러는 cleanup에서 해제한다. 이미지 로드 등 비동기 작업은 실패 경로도 처리한다.

## 타입

- 공유 타입은 `src/type/`에 도메인별로 정의하고 다른 모듈을 import하지 않는다.
- API 요청·응답 타입은 백엔드 DTO의 구조·필드명과 일치시킨다.
- 운영 약관 본문·버전·시행일·필수 여부는 `GET /member/consent` API에서 읽는다. 프런트 번들에 원문을 포함하지 않는다.
  오픈소스 라이선스 문서는 의존성과 함께 빌드에 포함한다.
- 객체 타입은 `interface`를 우선하고, 유니온·교차 타입은 `type`을 사용한다.
- Props는 컴포넌트 파일 상단에 정의한다.

## 스타일

- CSS Module은 `s`로 import한다: `import s from './Header.module.css'`.
- 조건부 클래스는 템플릿 리터럴을 사용한다: `` `${s.btn} ${isActive ? s.active : ''}` ``.
- 전역 스타일과 reset은 `App.css`에 작성하고 `App.tsx`에서 import한다. 컴포넌트 스타일은 CSS Module에 둔다.
- 루트 폰트 크기는 `62.5%`로 설정한다. 기본 브라우저 설정에서 `1rem = 10px`이다.
- 기본 레이아웃은 모바일 기준으로 작성하고, 크기별 분기는 아래 기준을 사용한다. 미디어쿼리의 크기 단위는 `px`로 쓴다.

| 조건 | 용도 |
|---|---|
| `(min-width: 576px)` | 넓은 화면 레이아웃 |
| `(max-height: 780px)` | 높이가 낮은 화면의 여백 보정 |

모바일에만 높이 보정을 적용하려면 `(max-width: 575px) and (max-height: 780px)`로 제한한다.
`hover`, `prefers-reduced-motion`처럼 입력 방식·접근성을 위한 조건은 별도로 사용할 수 있다.

## 키보드와 입력 레이아웃

- iOS 키보드의 리사이즈·보조바·높이 구독은 앱 공통 훅에서만 관리한다. 페이지와 입력 컴포넌트에서 네이티브 설정을 변경하거나 종료 시 복원하지 않는다.
- iOS 문서는 고정하고 `app-scroll` 안에서 페이지를 스크롤한다. 페이지 위치는 `getPageScrollElement()`로 접근한다.
- 일반 `input`·`textarea`는 앱 공통 처리가 안쪽부터 실제로 스크롤되는 영역을 찾아 가려진 만큼만 이동시킨다. `textarea`는 편집 중인 줄을 기준으로 한다. 별도 키보드 훅이나 `focus`·문서 `scrollTo` 보정을 추가하지 않는다.
- 작은 입력 모달은 `MiniModal`을 사용한다. 직접 만드는 작은 모달은 이동할 패널에 `data-keyboard-modal`을 지정한다.
- 채팅처럼 입력 영역을 직접 배치하는 특수 레이아웃만 `data-keyboard-managed`로 기본 보정을 제외하고 공통 `keyboardStore`를 소비한다. 모달·스크롤 영역 밖에 새 입력 레이아웃을 만들면 공통 처리에서 가시성을 검증한다.
- 배경 높이는 `--app-viewport-height`를 사용한다. iOS 키보드 이동 중 배경을 축소하거나 문서 위치를 강제로 복원하지 않는다.

## 이미지

- WebP를 기본으로 사용한다. 사진·일러스트는 손실 q90, 그라데이션·픽셀아트·플랫 그래픽·로고는 무손실로 변환한다.
- 변환 명령: `npm run webp -- [--lossless | --quality N] <파일...>`.
- 손실 변환 후 실기기에서 화질을 확인한다. 20KB 이하 소형 에셋은 변환을 생략할 수 있다.

## 주석과 빈 줄

- 주석은 한국어로 작성한다. 코드에서 드러나지 않는 의도·제약·예외를 설명하고, 이름만 반복하는 주석은 생략한다.
- 훅의 사용법이 이름만으로 분명하지 않으면 정의 위에 역할·주요 반환값·주의사항을 짧게 적는다. 내부 함수마다 주석을 강제하지 않는다.
- import와 본문 사이는 빈 줄 3개, 최상위 정의 사이는 2개, 함수 내부의 논리 단계·섹션 사이는 1개를 둔다.
- 같은 의미 단위의 연속 선언에는 빈 줄을 넣지 않는다. 본문 안에서는 빈 줄 3개를 사용하지 않는다.
