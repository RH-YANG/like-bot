from fastapi import HTTPException, status

import database.dao.targeting_set_dao as targeting_set_dao
import database.dao.target_keyword_dao as target_keyword_dao
from config.platform import PLATFORM_CONFIG
from database.dbms_control import connect_db
from database.schema import TargetingSet, TargetKeyword
from database.dto import TargetingSetResponse



# ========== 타겟팅 세트와 키워드 ==========



def clean_keyword_list(keyword_list):
    # → 공백을 정리하고 빈 값과 중복을 제거한다(입력 순서 유지)
    cleaned_keyword_list = []
    for keyword in keyword_list:
        cleaned_keyword = keyword.strip()
        if cleaned_keyword and cleaned_keyword not in cleaned_keyword_list:
            cleaned_keyword_list.append(cleaned_keyword)

    return cleaned_keyword_list



def validate_request(request):
    # → 저장 요청 값을 검증한다. 실패하면 400
    message = None
    if not request.name.strip():
        message = '이름을 입력해 주세요.'
    elif request.platform not in PLATFORM_CONFIG:
        message = '아직 지원하지 않는 플랫폼이에요.'
    elif not clean_keyword_list(request.search_keyword_list):
        message = '검색어를 하나 이상 입력해 주세요.'
    elif request.goal_count < 1 or request.max_scan_count < 1:
        message = '목표 개수와 최대 검토 수는 1 이상이어야 해요.'
    elif request.max_scan_count < request.goal_count:
        message = '최대 검토 수는 목표 개수보다 커야 해요.'
    elif request.max_post_age_hour is not None and request.max_post_age_hour < 1:
        message = '게시 후 경과 시간은 1시간 이상이어야 해요.'
    elif request.max_like_count is not None and request.max_like_count < 0:
        message = '좋아요 수 상한은 0 이상이어야 해요.'
    elif request.max_run_minute < 1:
        message = '최대 실행 시간은 1분 이상이어야 해요.'
    elif request.author_cooldown_day < 0:
        message = '작성자 쿨다운은 0일 이상이어야 해요.'

    if message is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)



def build_targeting_set(request, targeting_set_id=None):
    # → 저장 요청을 테이블 모델로 바꾼다
    targeting_set = TargetingSet(
        id=targeting_set_id,
        name=request.name.strip(),
        platform=request.platform,
        goal_count=request.goal_count,
        max_scan_count=request.max_scan_count,
        max_run_minute=request.max_run_minute,
        max_post_age_hour=request.max_post_age_hour,
        max_like_count=request.max_like_count,
        language=request.language,
        is_verified_excluded=request.is_verified_excluded,
        author_cooldown_day=request.author_cooldown_day,
    )

    return targeting_set



def insert_keyword(cur, targeting_set_id, request):
    # → 검색어·제외 키워드를 저장한다
    keyword_group = {
        'search': clean_keyword_list(request.search_keyword_list),
        'exclude': clean_keyword_list(request.exclude_keyword_list),
    }
    for keyword_type, keyword_list in keyword_group.items():
        for keyword in keyword_list:
            target_keyword = TargetKeyword(targeting_set_id=targeting_set_id, type=keyword_type, keyword=keyword)
            target_keyword_dao.insert(cur, target_keyword)



def build_response(targeting_set, target_keyword_list):
    # → 세트와 키워드를 응답 모델로 합친다
    search_keyword_list = [k.keyword for k in target_keyword_list if k.type == 'search']
    exclude_keyword_list = [k.keyword for k in target_keyword_list if k.type == 'exclude']
    targeting_set_field = targeting_set.model_dump()
    targeting_set_response = TargetingSetResponse(
        **targeting_set_field,
        search_keyword_list=search_keyword_list,
        exclude_keyword_list=exclude_keyword_list,
    )

    return targeting_set_response



def select_targeting_set_response(cur, targeting_set_id):
    # → 세트 1건을 키워드와 함께 조회한다. 없으면 None
    targeting_set = targeting_set_dao.select_by_id(cur, targeting_set_id)
    if targeting_set is None:
        return None

    target_keyword_list = target_keyword_dao.select_by_targeting_set_id(cur, targeting_set_id)
    targeting_set_response = build_response(targeting_set, target_keyword_list)

    return targeting_set_response



@connect_db
def select_targeting_set_list(conn, cur):
    # → 전체 세트를 키워드와 함께 조회한다
    targeting_set_response_list = []
    for targeting_set in targeting_set_dao.select_all(cur):
        target_keyword_list = target_keyword_dao.select_by_targeting_set_id(cur, targeting_set.id)
        targeting_set_response = build_response(targeting_set, target_keyword_list)
        targeting_set_response_list.append(targeting_set_response)

    return targeting_set_response_list



@connect_db
def select_targeting_set(conn, cur, targeting_set_id):
    # → 세트 1건을 조회한다. 없으면 404
    targeting_set_response = select_targeting_set_response(cur, targeting_set_id)
    if targeting_set_response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='타겟팅 세트를 찾을 수 없어요.')

    return targeting_set_response



@connect_db
def create_targeting_set(conn, cur, request):
    # → 세트와 키워드를 함께 저장한다
    validate_request(request)

    targeting_set = build_targeting_set(request)
    targeting_set_id = targeting_set_dao.insert(cur, targeting_set)
    insert_keyword(cur, targeting_set_id, request)

    conn.commit()

    return targeting_set_id



@connect_db
def update_targeting_set(conn, cur, targeting_set_id, request):
    # → 세트를 수정하고 키워드를 요청 내용으로 교체한다
    validate_request(request)

    targeting_set = build_targeting_set(request, targeting_set_id)
    updated_count = targeting_set_dao.update(cur, targeting_set)
    if updated_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='타겟팅 세트를 찾을 수 없어요.')

    target_keyword_dao.delete_by_targeting_set_id(cur, targeting_set_id)
    insert_keyword(cur, targeting_set_id, request)

    conn.commit()

    return targeting_set_id



@connect_db
def delete_targeting_set(conn, cur, targeting_set_id):
    # → 세트를 삭제한다. 키워드는 함께 삭제되고 실행 이력은 snapshot으로 남는다
    deleted_count = targeting_set_dao.delete(cur, targeting_set_id)
    if deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='타겟팅 세트를 찾을 수 없어요.')

    conn.commit()
