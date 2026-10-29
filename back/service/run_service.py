from dataclasses import asdict
from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation

import service.targeting_service as targeting_service
import service.post_service as post_service
import database.dao.run_dao as run_dao
import database.dao.post_dao as post_dao
from config.platform import PLATFORM_CONFIG
from database.dbms_control import connect_db
from database.schema import Run, TargetingSet
from database.schema_enum import RunMode, RunStatus, RunEndReason, PostStatus
from database.dto import RunResponse



# ========== 실행 생성·상태 전이·진행 기록 ==========



RUN_LIST_LIMIT = 50
STALE_HEARTBEAT_SECOND = 300                         # heartbeat가 이 시간 이상 끊기면 interrupted로 정리
BROWSER_STATUS_LIST = [RunStatus.RUNNING, RunStatus.STOPPING]
ACTIVE_CONFLICT_MESSAGE = '같은 플랫폼에서 진행 중인 실행이 있어요. 끝난 뒤 다시 시도해 주세요.'
# 세트에 컬럼이 추가되기 전에 만든 실행의 snapshot은 테이블 모델 기본값으로 채운다
TARGETING_SET_DEFAULT = {name: field.default for name, field in TargetingSet.model_fields.items() if not field.is_required()}



def build_targeting_snapshot(targeting_set_response, platform_config):
    # → 실행 시점의 세트·키워드·플랫폼 설정을 jsonb로 저장할 사본으로 만든다
    targeting_snapshot = {
        'targeting_set': targeting_set_response.model_dump(mode='json'),
        'platform_config': asdict(platform_config),
    }

    return targeting_snapshot



def read_targeting_set(targeting_snapshot):
    # → snapshot의 세트 값을 읽는다. 나중에 추가된 항목은 기본값으로 채운다
    targeting_set = {**TARGETING_SET_DEFAULT, **targeting_snapshot['targeting_set']}

    return targeting_set



def build_run_response(run_row):
    # → 실행 조회 결과(후보·승인 수 포함)를 응답 모델로 바꾼다. 목표 개수와 세트 이름은 snapshot에서 읽는다
    targeting_set = read_targeting_set(run_row['targeting_snapshot'])
    run_response = RunResponse(
        **run_row,
        targeting_set_name=targeting_set['name'],
        goal_count=targeting_set['goal_count'],
        max_scan_count=targeting_set['max_scan_count'],
    )

    return run_response



def delete_unfinished_post(cur, run_id):
    # → 끝난 실행에 남은 후보·승인 대기 글을 지운다. 좋아요하지 않은 글이므로 이후 실행에서 다시 찾을 수 있게 한다
    for post_status in (PostStatus.CANDIDATE, PostStatus.APPROVED):
        post_dao.delete_by_run_status(cur, run_id, post_status)



def finish_stale_run(cur, stale_second):
    # → heartbeat가 끊긴 실행을 interrupted로 종료하고 남은 글을 정리한다
    finished_run_id_list = run_dao.finish_stale(cur, BROWSER_STATUS_LIST, stale_second, RunEndReason.INTERRUPTED)
    for run_id in finished_run_id_list:
        delete_unfinished_post(cur, run_id)

    return finished_run_id_list



def select_run_for_update(cur, run_id):
    # → 실행을 잠그고 조회한다. 없으면 404
    run = run_dao.select_by_id(cur, run_id, is_for_update=True)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='실행 기록을 찾을 수 없어요.')

    return run



# ---------- API ----------
@connect_db
def create_run(conn, cur, request):
    # → 타겟팅 세트로 실행을 등록한다. worker가 pending 실행을 가져가 처리한다
    # 1. heartbeat가 끊긴 실행 정리
    finish_stale_run(cur, STALE_HEARTBEAT_SECOND)

    # 2. 세트와 플랫폼 확인
    targeting_set_response = targeting_service.select_targeting_set_response(cur, request.targeting_set_id)
    if targeting_set_response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='타겟팅 세트를 찾을 수 없어요.')

    platform_config = PLATFORM_CONFIG.get(targeting_set_response.platform)
    if platform_config is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='아직 지원하지 않는 플랫폼이에요.')

    # 3. 실행 저장. 같은 플랫폼에 진행 중인 실행이 있으면 부분 UNIQUE 인덱스가 막는다
    targeting_snapshot = build_targeting_snapshot(targeting_set_response, platform_config)
    run = Run(
        targeting_set_id=request.targeting_set_id,
        platform=targeting_set_response.platform,
        mode=request.mode,
        status=RunStatus.PENDING,
        targeting_snapshot=targeting_snapshot,
    )
    try:
        run_id = run_dao.insert(cur, run)
    except UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ACTIVE_CONFLICT_MESSAGE)

    conn.commit()

    return run_id



@connect_db
def select_run_list(conn, cur):
    # → 최근 실행 목록. 조회 전에 끊긴 실행을 정리한다
    finish_stale_run(cur, STALE_HEARTBEAT_SECOND)
    conn.commit()

    run_response_list = [build_run_response(run_row) for run_row in run_dao.select_with_post_count(cur, None, RUN_LIST_LIMIT)]

    return run_response_list



@connect_db
def select_run_detail(conn, cur, run_id):
    # → 실행 1건과 그 실행에서 판정한 게시글 목록
    run_row_list = run_dao.select_with_post_count(cur, run_id, 1)
    if not run_row_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='실행 기록을 찾을 수 없어요.')

    run_response = build_run_response(run_row_list[0])
    post_response_list = post_service.select_post_response_list(cur, run_id, None, None)

    return run_response, post_response_list



@connect_db
def stop_run(conn, cur, run_id):
    # → 실행을 중지한다. 브라우저 작업 중이면 stopping으로 바꾸고 worker가 마무리한다
    run = select_run_for_update(cur, run_id)

    if run.status == RunStatus.PENDING:
        run_dao.finish(cur, run_id, [RunStatus.PENDING], RunEndReason.USER_STOPPED, None)
    elif run.status == RunStatus.AWAITING_APPROVAL:
        delete_unfinished_post(cur, run_id)
        run_dao.finish(cur, run_id, [RunStatus.AWAITING_APPROVAL], RunEndReason.USER_STOPPED, None)
    elif run.status == RunStatus.RUNNING:
        run_dao.update_status(cur, run_id, [RunStatus.RUNNING], RunStatus.STOPPING)
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='이미 끝났거나 중지하는 중이에요.')

    conn.commit()



@connect_db
def approve_run(conn, cur, run_id, approved_post_id_list):
    # → 후보 승인 결과를 저장하고, 승인한 글이 있으면 좋아요 단계를 다시 대기열에 올린다
    # 1. 승인 대기 상태 확인
    run = select_run_for_update(cur, run_id)
    if run.status != RunStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='승인을 기다리는 실행이 아니에요.')

    # 2. 승인·거절 반영
    post_dao.update_run_candidate(cur, run_id, approved_post_id_list)
    approved_count = post_dao.count_by_run_status(cur, run_id, PostStatus.APPROVED)

    # 3. 승인한 글이 없으면 종료, 있으면 좋아요 단계 대기
    if approved_count == 0:
        run_dao.finish(cur, run_id, [RunStatus.AWAITING_APPROVAL], RunEndReason.NONE_APPROVED, None)
    else:
        try:
            run_dao.update_status(cur, run_id, [RunStatus.AWAITING_APPROVAL], RunStatus.PENDING)
        except UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ACTIVE_CONFLICT_MESSAGE)

    conn.commit()

    return approved_count



# ---------- worker ----------
@connect_db
def recover_interrupted_run(conn, cur):
    # → worker 시작 시 이전 프로세스가 남긴 진행 중 실행을 interrupted로 종료한다
    finished_run_id_list = finish_stale_run(cur, 0)

    conn.commit()

    return finished_run_id_list



@connect_db
def claim_pending_run(conn, cur):
    # → 가장 오래된 pending 실행을 running으로 바꿔 가져온다. 없으면 None
    run = run_dao.claim_pending(cur)

    conn.commit()

    return run



@connect_db
def touch_run_heartbeat(conn, cur, run_id):
    # → heartbeat를 갱신하고 현재 상태를 돌려준다(중지 요청 확인용)
    run_status = run_dao.update_heartbeat(cur, run_id)

    conn.commit()

    return run_status



@connect_db
def update_run_progress(conn, cur, run_id, scanned_count, liked_count, skip_count):
    # → 진행 숫자와 heartbeat를 갱신한다
    run_dao.update_progress(cur, run_id, scanned_count, liked_count, skip_count)

    conn.commit()



@connect_db
def finish_run(conn, cur, run_id, end_reason, error_message=None):
    # → 브라우저 작업 중인 실행을 종료하고 좋아요하지 않은 후보·승인 글을 정리한다
    finished_count = run_dao.finish(cur, run_id, BROWSER_STATUS_LIST, end_reason, error_message)
    if finished_count > 0:
        delete_unfinished_post(cur, run_id)

    conn.commit()



@connect_db
def wait_for_approval(conn, cur, run_id):
    # → 후보 수집을 마친 실행을 승인 대기로 바꾼다. 그사이 중지 요청이 들어왔으면 바꾸지 않고 0을 돌려준다
    updated_count = run_dao.update_status(cur, run_id, [RunStatus.RUNNING], RunStatus.AWAITING_APPROVAL)

    conn.commit()

    return updated_count



@connect_db
def is_like_phase(conn, cur, run):
    # → 승인 모드에서 승인한 글이 있으면 좋아요 단계다
    approved_count = post_dao.count_by_run_status(cur, run.id, PostStatus.APPROVED)
    is_like_phase_run = run.mode == RunMode.APPROVAL and approved_count > 0

    return is_like_phase_run
