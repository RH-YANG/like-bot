-- like-bot DB 스키마 스냅샷
-- 빈 DB 볼륨의 최초 기동에서 자동 적용된다. 이후 변경은 db/db_style.md의 절차를 따른다.



CREATE TABLE targeting_set (
    id                   integer GENERATED ALWAYS AS IDENTITY,
    name                 character varying NOT NULL,                                     -- 프론트 표기용 이름
    platform             character varying NOT NULL,                                     -- threads | instagram | x
    goal_count           integer NOT NULL DEFAULT 50,                                    -- 실행 1회 목표 좋아요 수
    max_scan_count       integer NOT NULL DEFAULT 500,                                   -- 실행 1회 최대 검토 게시글 수
    max_run_minute       integer NOT NULL DEFAULT 150,                                   -- 실행 1회 최대 시간(분)
    max_post_age_hour    integer DEFAULT 72,                                             -- 게시 후 경과 시간 상한, NULL이면 제한 없음
    max_like_count       integer,                                                        -- 게시글 좋아요 수 상한, NULL이면 제한 없음
    language             character varying NOT NULL DEFAULT 'ko',                        -- ko | ja | en (ISO 639-1)
    is_verified_excluded boolean NOT NULL DEFAULT true,                                  -- 인증 배지 계정 제외
    author_cooldown_day  integer NOT NULL DEFAULT 14,                                    -- 같은 작성자에게 다시 좋아요하기까지 최소 일수
    created_at           timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT targeting_set_pk PRIMARY KEY (id)
);
COMMENT ON TABLE targeting_set IS '프런트에서 조작하는 타겟팅 조건 묶음. 삭제해도 실행 이력은 run.targeting_snapshot으로 남는다.';



CREATE TABLE target_keyword (
    id               integer GENERATED ALWAYS AS IDENTITY,
    targeting_set_id integer NOT NULL,
    type             character varying NOT NULL,                                         -- search: 검색어로 사용 | exclude: 본문에 포함되면 제외
    keyword          character varying NOT NULL,
    created_at       timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT target_keyword_pk PRIMARY KEY (id),
    CONSTRAINT target_keyword_fk FOREIGN KEY (targeting_set_id) REFERENCES targeting_set(id) ON DELETE CASCADE,
    CONSTRAINT target_keyword_targeting_set_id_type_keyword_uk UNIQUE (targeting_set_id, type, keyword)
);
COMMENT ON TABLE target_keyword IS '타겟팅 세트의 검색어와 제외 키워드. 세트 삭제 시 함께 삭제된다.';



CREATE TABLE author (
    id           integer GENERATED ALWAYS AS IDENTITY,
    platform     character varying NOT NULL,                                             -- threads | instagram | x
    handle       character varying NOT NULL,                                             -- 계정 아이디(@ 제외)
    display_name character varying,                                                      -- 프로필 이름
    is_verified  boolean NOT NULL DEFAULT false,                                         -- 인증 배지 계정 여부
    is_blocked   boolean NOT NULL DEFAULT false,                                         -- 수동 제외 계정(브랜드·지인 등)
    memo         character varying,                                                      -- 관리자 메모
    created_at   timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT author_pk PRIMARY KEY (id),
    CONSTRAINT author_platform_handle_uk UNIQUE (platform, handle)
);
COMMENT ON TABLE author IS '좋아요 대상으로 판정된 게시글의 작성자. 쿨다운과 수동 제외의 기준이다.';



CREATE TABLE run (
    id                 integer GENERATED ALWAYS AS IDENTITY,
    targeting_set_id   integer,                                                          -- 세트 삭제 시 NULL
    platform           character varying NOT NULL,                                       -- threads | instagram | x
    mode               character varying NOT NULL DEFAULT 'auto',                        -- auto: 바로 좋아요 | approval: 승인한 글만 좋아요
    status             character varying NOT NULL DEFAULT 'pending',                     -- pending | running | awaiting_approval | stopping | finished
    end_reason         character varying,                                                -- goal_reached | search_exhausted | max_scan_reached | max_duration_reached | limit_reached | none_approved | user_stopped | login_required | challenge_detected | action_blocked | interrupted | error
    targeting_snapshot jsonb NOT NULL,                                                   -- 실행 시점의 타겟팅 세트·키워드·플랫폼 설정 사본
    scanned_count      integer NOT NULL DEFAULT 0,                                       -- 검토한 게시글 수
    liked_count        integer NOT NULL DEFAULT 0,                                       -- 실제로 좋아요를 누른 수
    skip_count         jsonb NOT NULL DEFAULT '{}',                                      -- 건너뛴 이유별 개수 {skip_reason: count}
    error_message      character varying,
    heartbeat_at       timestamp with time zone,                                         -- 실행 루프 생존 확인, 끊기면 interrupted로 종료
    started_at         timestamp with time zone,
    finished_at        timestamp with time zone,
    created_at         timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT run_pk PRIMARY KEY (id),
    CONSTRAINT run_fk FOREIGN KEY (targeting_set_id) REFERENCES targeting_set(id) ON DELETE SET NULL
);
COMMENT ON TABLE run IS '실행 버튼 1회의 기록. 실행 조건은 targeting_snapshot에서 읽는다.';
-- 플랫폼당 브라우저를 쓰는 실행은 1개만 허용한다. 승인 대기(awaiting_approval)는 브라우저를 쓰지 않으므로 제외한다.
CREATE UNIQUE INDEX run_platform_uk ON run (platform) WHERE status IN ('pending', 'running', 'stopping');
CREATE INDEX run_targeting_set_id_idx ON run (targeting_set_id);



CREATE TABLE post (
    id             integer GENERATED ALWAYS AS IDENTITY,
    run_id         integer NOT NULL,                                                     -- 이 글을 판정한 실행
    author_id      integer NOT NULL,
    platform       character varying NOT NULL,                                           -- threads | instagram | x
    post_code      character varying NOT NULL,                                           -- URL의 게시글 코드(Threads·Instagram) 또는 ID(X)
    content        character varying,
    posted_at      timestamp with time zone,
    like_count     integer,                                                              -- 판정 시점 좋아요 수
    search_keyword character varying NOT NULL,                                           -- 이 글을 찾은 검색어
    status         character varying NOT NULL,                                           -- candidate | approved | rejected | liked | failed
    liked_at       timestamp with time zone,                                             -- 상한·쿨다운 계산 기준
    created_at     timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT post_pk PRIMARY KEY (id),
    CONSTRAINT post_fk_1 FOREIGN KEY (run_id) REFERENCES run(id),
    CONSTRAINT post_fk_2 FOREIGN KEY (author_id) REFERENCES author(id),
    CONSTRAINT post_platform_post_code_uk UNIQUE (platform, post_code)
);
COMMENT ON TABLE post IS '좋아요 대상으로 판정된 게시글. 건너뛴 글은 저장하지 않고 run.skip_count에 개수만 남긴다.';
CREATE INDEX post_run_id_idx ON post (run_id);
CREATE INDEX post_author_id_idx ON post (author_id);
CREATE INDEX post_liked_at_idx ON post (liked_at);
