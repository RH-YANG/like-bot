from fastapi import APIRouter

import service.targeting_service as targeting_service
from database.dto import SaveTargetingSetRequest, SaveTargetingSetResponse, TargetingSetResponse, TargetingSetListResponse



# ========== 타겟팅 세트 API ==========



router = APIRouter(prefix='/targeting', tags=['targeting'])



@router.get('', response_model=TargetingSetListResponse)
def get_targeting_set_list():
    '''전체 타겟팅 세트를 검색어·제외 키워드와 함께 반환한다.'''
    targeting_set_response_list = targeting_service.select_targeting_set_list()

    targeting_set_list = TargetingSetListResponse(targeting_set_list=targeting_set_response_list)

    return targeting_set_list



@router.get('/{targeting_set_id}', response_model=TargetingSetResponse)
def get_targeting_set(targeting_set_id: int):
    '''타겟팅 세트 1건. 없으면 404.'''
    targeting_set = targeting_service.select_targeting_set(targeting_set_id)

    return targeting_set



@router.post('', response_model=SaveTargetingSetResponse)
def post_targeting_set(request: SaveTargetingSetRequest):
    '''타겟팅 세트를 만든다. 검색어가 없거나 값이 잘못되면 400.'''
    targeting_set_id = targeting_service.create_targeting_set(request)

    saved_targeting_set = SaveTargetingSetResponse(targeting_set_id=targeting_set_id)

    return saved_targeting_set



@router.put('/{targeting_set_id}', response_model=SaveTargetingSetResponse)
def put_targeting_set(targeting_set_id: int, request: SaveTargetingSetRequest):
    '''타겟팅 세트를 수정하고 키워드를 요청 내용으로 교체한다. 진행 중 실행은 snapshot을 쓰므로 영향이 없다.'''
    targeting_set_id = targeting_service.update_targeting_set(targeting_set_id, request)

    saved_targeting_set = SaveTargetingSetResponse(targeting_set_id=targeting_set_id)

    return saved_targeting_set



@router.delete('/{targeting_set_id}')
def delete_targeting_set(targeting_set_id: int):
    '''타겟팅 세트를 삭제한다. 실행 이력은 snapshot으로 남는다.'''
    targeting_service.delete_targeting_set(targeting_set_id)
