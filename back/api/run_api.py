from fastapi import APIRouter

import service.run_service as run_service
from database.dto import CreateRunRequest, CreateRunResponse, ApproveRunRequest, RunListResponse, RunDetailResponse



# ========== 실행 API ==========



router = APIRouter(prefix='/run', tags=['run'])



@router.get('', response_model=RunListResponse)
def get_run_list():
    '''최근 실행 목록. heartbeat가 끊긴 실행은 조회 전에 interrupted로 정리된다.'''
    run_response_list = run_service.select_run_list()

    run_list = RunListResponse(run_list=run_response_list)

    return run_list



@router.get('/{run_id}', response_model=RunDetailResponse)
def get_run_detail(run_id: int):
    '''실행 1건과 판정한 게시글(후보·승인·좋아요·실패·거절) 목록.'''
    run_response, post_response_list = run_service.select_run_detail(run_id)

    run_detail = RunDetailResponse(run=run_response, post_list=post_response_list)

    return run_detail



@router.post('', response_model=CreateRunResponse)
def post_run(request: CreateRunRequest):
    '''실행을 등록한다. 같은 플랫폼에 진행 중인 실행이 있으면 409.'''
    run_id = run_service.create_run(request)

    created_run = CreateRunResponse(run_id=run_id)

    return created_run



@router.post('/{run_id}/stop')
def post_run_stop(run_id: int):
    '''실행을 중지한다. 브라우저 작업 중이면 현재 동작을 마무리한 뒤 끝난다.'''
    run_service.stop_run(run_id)



@router.post('/{run_id}/approval')
def post_run_approval(run_id: int, request: ApproveRunRequest):
    '''승인한 후보에만 좋아요를 누르도록 실행을 다시 대기열에 올린다. 목록에 없는 후보는 거절된다.'''
    run_service.approve_run(run_id, request.approved_post_id_list)
