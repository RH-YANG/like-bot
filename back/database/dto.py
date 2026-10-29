from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from database.schema_enum import Platform, RunMode, RunStatus, RunEndReason, PostStatus



# ========== API 요청·응답 모델 ==========



class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )



# ---------- 타겟팅 세트 ----------
class SaveTargetingSetRequest(ApiModel):
    name: str
    platform: Platform
    goal_count: int
    max_scan_count: int
    max_run_minute: int = 150
    max_post_age_hour: Optional[int] = None
    max_like_count: Optional[int] = None
    language: Literal['ko', 'ja', 'en'] = 'ko'
    is_verified_excluded: bool = True
    author_cooldown_day: int = 14
    search_keyword_list: list[str]
    exclude_keyword_list: list[str] = []



class TargetingSetResponse(ApiModel):
    id: int
    name: str
    platform: Platform
    goal_count: int
    max_scan_count: int
    max_run_minute: int
    max_post_age_hour: Optional[int] = None
    max_like_count: Optional[int] = None
    language: str
    is_verified_excluded: bool
    author_cooldown_day: int
    search_keyword_list: list[str]
    exclude_keyword_list: list[str]
    created_at: datetime
    updated_at: datetime



class TargetingSetListResponse(ApiModel):
    targeting_set_list: list[TargetingSetResponse]



class SaveTargetingSetResponse(ApiModel):
    targeting_set_id: int



# ---------- 실행 ----------
class CreateRunRequest(ApiModel):
    targeting_set_id: int
    mode: RunMode = RunMode.AUTO



class CreateRunResponse(ApiModel):
    run_id: int



class ApproveRunRequest(ApiModel):
    approved_post_id_list: list[int]



class RunResponse(ApiModel):
    id: int
    targeting_set_id: Optional[int] = None
    targeting_set_name: str                          # 실행 시점 이름(snapshot)
    platform: Platform
    mode: RunMode
    status: RunStatus
    end_reason: Optional[RunEndReason] = None
    goal_count: int                                  # 실행 시점 목표(snapshot)
    max_scan_count: int
    scanned_count: int
    liked_count: int
    candidate_count: int                             # 승인 대기 중인 후보 수
    approved_count: int                              # 승인 후 좋아요를 기다리는 글 수
    skip_count: dict
    error_message: Optional[str] = None
    heartbeat_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime



class RunListResponse(ApiModel):
    run_list: list[RunResponse]



# ---------- 게시글 ----------
class PostResponse(ApiModel):
    id: int
    run_id: int
    platform: Platform
    post_code: str
    url: str
    content: Optional[str] = None
    posted_at: Optional[datetime] = None
    like_count: Optional[int] = None
    search_keyword: str
    status: PostStatus
    liked_at: Optional[datetime] = None
    created_at: datetime
    author_id: int
    author_handle: str
    author_display_name: Optional[str] = None
    is_author_blocked: bool



class PostListResponse(ApiModel):
    post_list: list[PostResponse]



class RunDetailResponse(ApiModel):
    run: RunResponse
    post_list: list[PostResponse]



# ---------- 작성자 ----------
class AuthorResponse(ApiModel):
    id: int
    platform: Platform
    handle: str
    url: str
    display_name: Optional[str] = None
    is_verified: bool
    is_blocked: bool
    memo: Optional[str] = None
    liked_post_count: int
    last_liked_at: Optional[datetime] = None
    created_at: datetime



class AuthorListResponse(ApiModel):
    author_list: list[AuthorResponse]



class UpdateAuthorRequest(ApiModel):
    is_blocked: bool
    memo: Optional[str] = None



# ---------- 좋아요 사용량(플랫폼별 상한과 최근 좋아요 수) ----------
class LikeUsageResponse(ApiModel):
    platform: Platform
    daily_like_limit: int
    hourly_like_limit: int
    daily_liked_count: int                           # 최근 24시간 좋아요 수
    hourly_liked_count: int                          # 최근 1시간 좋아요 수
    min_interval_sec: int
    max_interval_sec: int



class LikeUsageListResponse(ApiModel):
    like_usage_list: list[LikeUsageResponse]
