import logging
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import service.run_service as run_service
import service.post_service as post_service
import env
from database.schema_enum import RunMode, RunStatus, RunEndReason, PostStatus
from util.handler.platform_exception import LoginRequiredError, ChallengeDetectedError, ActionBlockedError



# ========== 실행 1건 처리 (검색 → 판정 → 좋아요 / 후보 수집 → 승인한 글 좋아요) ==========



logger = logging.getLogger('like_job')

WAIT_CHECK_SEC = 5                                   # 대기 중 중지 요청·heartbeat 확인 주기
LIMIT_RECHECK_SEC = 60                               # 시간당 상한에 걸렸을 때 다시 확인하는 주기
ERROR_MESSAGE_LENGTH = 1000
RISK_END_REASON = {
    LoginRequiredError: RunEndReason.LOGIN_REQUIRED,
    ChallengeDetectedError: RunEndReason.CHALLENGE_DETECTED,
    ActionBlockedError: RunEndReason.ACTION_BLOCKED,
}
# 승인 모드 수집 단계가 이 이유로 끝나면 모은 후보를 승인 대기로 넘긴다
COLLECT_DONE_REASON = {
    RunEndReason.GOAL_REACHED,
    RunEndReason.SEARCH_EXHAUSTED,
    RunEndReason.MAX_SCAN_REACHED,
    RunEndReason.MAX_DURATION_REACHED,
}



class RunStop(Exception):
    def __init__(self, end_reason):
        super().__init__(end_reason)
        self.end_reason = end_reason



def touch_heartbeat_file():
    # worker 컨테이너 healthcheck가 이 파일의 수정 시각을 본다
    Path(env.HEARTBEAT_FILE).touch()



class RunContext:
    def __init__(self, run):
        platform_config = run.targeting_snapshot['platform_config']
        self.run = run
        self.targeting_set = run_service.read_targeting_set(run.targeting_snapshot)
        self.platform_config = platform_config
        self.scanned_count = run.scanned_count
        self.liked_count = run.liked_count
        self.skip_count = dict(run.skip_count)
        self.candidate_count = 0
        self.deadline = datetime.now(timezone.utc) + timedelta(minutes=self.targeting_set['max_run_minute'])
        self.next_like_at = 0.0



    def beat(self):
        # heartbeat를 남기고 중지 요청·실행 시간 초과를 확인한다
        touch_heartbeat_file()
        run_status = run_service.touch_run_heartbeat(self.run.id)
        if run_status != RunStatus.RUNNING:
            raise RunStop(RunEndReason.USER_STOPPED)
        if datetime.now(timezone.utc) >= self.deadline:
            raise RunStop(RunEndReason.MAX_DURATION_REACHED)



    def save_progress(self):
        touch_heartbeat_file()
        run_service.update_run_progress(self.run.id, self.scanned_count, self.liked_count, self.skip_count)



    def wait(self, second):
        # 중지 요청을 확인하며 기다린다
        end_at = time.monotonic() + second
        while True:
            remain_second = end_at - time.monotonic()
            if remain_second <= 0:
                break
            time.sleep(min(WAIT_CHECK_SEC, remain_second))
            self.beat()



    def wait_like_turn(self):
        # 1. 직전 좋아요와의 간격
        self.wait(self.next_like_at - time.monotonic())

        # 2. 일간 상한은 실행 종료, 시간당 상한은 자리가 날 때까지 대기
        platform = self.run.platform
        while True:
            daily_liked_count, hourly_liked_count = post_service.select_recent_like_count(platform)
            if daily_liked_count >= self.platform_config['daily_like_limit']:
                raise RunStop(RunEndReason.LIMIT_REACHED)
            if hourly_liked_count < self.platform_config['hourly_like_limit']:
                break

            logger.info('run %s: 시간당 상한 도달, %s초 뒤 다시 확인', self.run.id, LIMIT_RECHECK_SEC)
            self.wait(LIMIT_RECHECK_SEC)



    def record_like(self, post_id, is_liked):
        post_service.mark_post_result(post_id, is_liked)
        if is_liked:
            self.liked_count += 1
        interval_second = random.uniform(self.platform_config['min_interval_sec'], self.platform_config['max_interval_sec'])
        self.next_like_at = time.monotonic() + interval_second
        self.save_progress()
        logger.info('run %s: post %s %s (%s/%s)', self.run.id, post_id, 'liked' if is_liked else 'failed',
                    self.liked_count, self.targeting_set['goal_count'])



def collect_post(context, client):
    # → 검색어별 최근 게시글을 판정해 자동 모드는 바로 좋아요, 승인 모드는 후보로 모은다
    run = context.run
    goal_count = context.targeting_set['goal_count']
    search_keyword_list = list(context.targeting_set['search_keyword_list'])
    random.shuffle(search_keyword_list)

    for search_keyword in search_keyword_list:
        for threads_post in client.search(search_keyword):
            # 1. 중지·시간·검토 수 확인
            context.beat()
            if context.scanned_count >= context.targeting_set['max_scan_count']:
                raise RunStop(RunEndReason.MAX_SCAN_REACHED)
            context.scanned_count += 1

            # 2. 판정
            skip_reason = post_service.judge_post(run.platform, threads_post, context.targeting_set)
            if skip_reason is not None:
                context.skip_count[skip_reason] = context.skip_count.get(skip_reason, 0) + 1
                context.save_progress()
                continue

            # 3. 승인 모드: 후보 저장
            if run.mode == RunMode.APPROVAL:
                post_service.save_post(run.id, run.platform, threads_post, search_keyword, PostStatus.CANDIDATE)
                context.candidate_count += 1
                context.save_progress()
                if context.candidate_count >= goal_count:
                    raise RunStop(RunEndReason.GOAL_REACHED)
                continue

            # 4. 자동 모드: 기록을 먼저 남기고 좋아요
            post_id = post_service.save_post(run.id, run.platform, threads_post, search_keyword, PostStatus.APPROVED)
            context.wait_like_turn()
            is_liked = client.like_in_page(threads_post.post_code)
            context.record_like(post_id, is_liked)
            if context.liked_count >= goal_count:
                raise RunStop(RunEndReason.GOAL_REACHED)

    raise RunStop(RunEndReason.SEARCH_EXHAUSTED)



def like_approved_post(context, client):
    # → 승인 모드 2단계: 승인한 글의 페이지로 이동해 좋아요를 누른다
    for post_row in post_service.select_approved_post_row_list(context.run.id):
        context.beat()
        context.wait_like_turn()
        is_liked = client.like_post(post_row['author_handle'], post_row['post_code'])
        context.record_like(post_row['id'], is_liked)

    raise RunStop(RunEndReason.GOAL_REACHED)



def execute_run(run, client):
    # → 실행 1건을 단계에 맞게 처리하고 결과에 따라 종료하거나 승인 대기로 넘긴다
    # 1. 단계 판단
    context = RunContext(run)
    is_like_phase = run_service.is_like_phase(run)
    logger.info('run %s 시작: mode=%s, like_phase=%s', run.id, run.mode, is_like_phase)

    # 2. 처리
    end_reason = RunEndReason.ERROR
    error_message = None
    try:
        client.check_login()
        if is_like_phase:
            like_approved_post(context, client)
        else:
            collect_post(context, client)
    except RunStop as run_stop:
        end_reason = run_stop.end_reason
    except (LoginRequiredError, ChallengeDetectedError, ActionBlockedError) as risk_error:
        end_reason = RISK_END_REASON[type(risk_error)]
        error_message = str(risk_error)[:ERROR_MESSAGE_LENGTH]
    except Exception as error:
        logger.exception('run %s 처리 중 오류', run.id)
        error_message = f'{type(error).__name__}: {error}'[:ERROR_MESSAGE_LENGTH]


    # 3. 종료 또는 승인 대기
    context.save_progress()
    is_collect_done = run.mode == RunMode.APPROVAL and not is_like_phase and end_reason in COLLECT_DONE_REASON
    if is_collect_done and context.candidate_count > 0:
        updated_count = run_service.wait_for_approval(run.id)
        if updated_count == 0:
            run_service.finish_run(run.id, RunEndReason.USER_STOPPED)
        logger.info('run %s 승인 대기: 후보 %s개', run.id, context.candidate_count)
    else:
        run_service.finish_run(run.id, end_reason, error_message)
        logger.info('run %s 종료: %s', run.id, end_reason)
