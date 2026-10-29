from fastapi import APIRouter

import service.author_service as author_service
from database.dto import AuthorListResponse, UpdateAuthorRequest



# ========== 작성자 API ==========



router = APIRouter(prefix='/author', tags=['author'])



@router.get('', response_model=AuthorListResponse)
def get_author_list(is_blocked_only: bool = False):
    '''작성자 목록(최근 좋아요 순 300명). is_blocked_only면 제외 계정만.'''
    author_response_list = author_service.select_author_list(is_blocked_only)

    author_list = AuthorListResponse(author_list=author_response_list)

    return author_list



@router.patch('/{author_id}')
def patch_author(author_id: int, request: UpdateAuthorRequest):
    '''작성자 제외 여부와 메모를 수정한다. 제외하면 다음 실행부터 건너뛴다.'''
    author_service.update_author(author_id, request)
