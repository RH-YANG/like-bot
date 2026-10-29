from fastapi import HTTPException, status

import service.post_service as post_service
import database.dao.author_dao as author_dao
from database.dbms_control import connect_db
from database.dto import AuthorResponse



# ========== 작성자 조회·관리(제외·메모) ==========



AUTHOR_LIST_LIMIT = 300



@connect_db
def select_author_list(conn, cur, is_blocked_only):
    # → 작성자 목록을 좋아요 통계와 함께 조회한다
    author_response_list = []
    for author_row in author_dao.select_list_with_like_stat(cur, is_blocked_only, AUTHOR_LIST_LIMIT):
        profile_url = post_service.build_profile_url(author_row['platform'], author_row['handle'])
        author_response = AuthorResponse(**author_row, url=profile_url)
        author_response_list.append(author_response)

    return author_response_list



@connect_db
def update_author(conn, cur, author_id, request):
    # → 작성자 제외 여부와 메모를 수정한다. 요청에 memo가 없으면 기존 메모를 유지한다
    author = author_dao.select_by_id(cur, author_id)
    if author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='작성자를 찾을 수 없어요.')

    memo = author.memo
    if 'memo' in request.model_fields_set:
        memo = None
        if request.memo is not None and request.memo.strip():
            memo = request.memo.strip()

    author_dao.update_manage_field(cur, author_id, request.is_blocked, memo)

    conn.commit()
