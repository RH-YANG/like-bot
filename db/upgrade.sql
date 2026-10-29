-- 이번에 적용할 스키마 변경. 다음 변경 때 내용을 덮어쓴다(지난 변경은 Git 이력으로 확인)
-- 적용(프로젝트 루트, Git Bash 등):
--   docker exec -i lbt-db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < db/upgrade.sql

BEGIN;

-- 작성자 쿨다운·실행 시간 상한을 플랫폼 설정(config/platform.py)에서 타겟팅 세트로 옮긴다
ALTER TABLE targeting_set
    ADD COLUMN author_cooldown_day integer NOT NULL DEFAULT 14,
    ADD COLUMN max_run_minute      integer NOT NULL DEFAULT 150;

COMMIT;
