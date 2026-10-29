from typing import Optional
from fastapi import APIRouter, Query

import service.post_service as post_service
from database.schema_enum import PostStatus
from database.dto import PostListResponse, LikeUsageListResponse



# ========== 게시글 API ==========



router = APIRouter(prefix='/post', tags=['post'])



@router.get('', response_model=PostListResponse)
def get_post_list(status: Optional[list[PostStatus]] = Query(default=None)):
    '''게시글 훑어보기 목록(최근 200건). status를 여러 개 줄 수 있고, 없으면 전체 상태.'''
    post_response_list = post_service.select_post_list(status)

    post_list = PostListResponse(post_list=post_response_list)

    return post_list



@router.get('/like-usage', response_model=LikeUsageListResponse)
def get_like_usage_list():
    '''플랫폼별 좋아요 상한(config/platform.py)과 최근 24시간·1시간 좋아요 수.'''
    like_usage_response_list = post_service.select_like_usage_list()

    like_usage_list = LikeUsageListResponse(like_usage_list=like_usage_response_list)

    return like_usage_list
