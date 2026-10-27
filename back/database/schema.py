from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

from database.schema_enum import Platform, RunMode, RunStatus, RunEndReason, PostStatus



# ========== DB에 직접 구현된 테이블의 모델 ==========



class TargetingSet(BaseModel):
    '''
    프런트에서 조작하는 타겟팅 조건 묶음(검색어·게시글 조건·실행 분량).
    삭제해도 실행 이력은 run.targeting_snapshot으로 남는다.
    '''
    id: Optional[int] = None                    # PK
    name: str                                   # 프론트 표기용
    platform: Platform

    goal_count: int = 50                        # 실행 1회 목표 좋아요 수
    max_scan_count: int = 500                   # 실행 1회 최대 검토 게시글 수
    max_post_age_hour: Optional[int] = 72       # 게시 후 경과 시간 상한, None이면 제한 없음
    max_like_count: Optional[int] = None        # 반응이 적은 글 위주로 고를 때 사용, None이면 제한 없음
    language: Literal['ko', 'ja', 'en'] = 'ko'  # 대상 게시글 언어
    is_verified_excluded: bool = True           # 인증 배지 계정 제외

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None



class TargetKeyword(BaseModel):
    '''
    타겟팅 세트의 검색어와 제외 키워드.
    (targeting_set_id, type, keyword) UNIQUE.
    세트 삭제 시 함께 삭제(ON DELETE CASCADE).
    '''
    id: Optional[int] = None                     # PK
    targeting_set_id: int                        # FK
    type: Literal['search', 'exclude']           # 검색어로 포함인지 제외인지
    keyword: str
    created_at: Optional[datetime] = None



class Author(BaseModel):
    '''
    수집한 게시글의 작성자.
    (platform, handle) UNIQUE.
    '''
    id: Optional[int] = None                     # PK
    platform: Platform
    handle: str                                  # 계정 아이디(@ 제외)
    display_name: Optional[str] = None           # 프로필 이름
    is_verified: bool = False                    # 인증계정인지 여부
    is_blocked: bool = False                     # 수동 제외 계정(브랜드·지인 등)
    memo: Optional[str] = None                   # 관리자 메모
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None



class Run(BaseModel):
    '''
    1번 실행한 기록.
    플랫폼당 진행 중(pending·running·stopping) 실행은 1개만 허용(부분 UNIQUE 인덱스).
    승인 대기(awaiting_approval) 중에는 브라우저를 쓰지 않으므로 다른 실행을 막지 않는다.
    목표 개수 등 실행 조건은 targeting_snapshot에서 읽는다.
    '''
    id: Optional[int] = None                     # PK
    targeting_set_id: Optional[int] = None       # FK, 세트 삭제 시 NULL(ON DELETE SET NULL)
    platform: Platform
    mode: RunMode = RunMode.AUTO                 # auto: 바로 좋아요 | approval: 승인한 글만 좋아요
    status: RunStatus = RunStatus.PENDING        # 실행 상태
    end_reason: Optional[RunEndReason] = None
    targeting_snapshot: dict                     # 실행 시점의 타겟팅 세트·키워드·플랫폼 설정 사본(jsonb)

    scanned_count: int = 0                       # 검토한 게시글 수 (세트의 max_scan_count와 비교)
    liked_count: int = 0
    skip_count: dict = {}                        # 건너뛴 이유별 개수 {SkipReason 값: 개수} (jsonb)
    error_message: Optional[str] = None
    heartbeat_at: Optional[datetime] = None      # 실행 루프 생존 확인, 끊기면 interrupted로 종료
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None



class Post(BaseModel):
    '''
    좋아요 대상으로 판정된 게시글.
    건너뛴 글은 저장하지 않고 run.skip_count에 개수만 남긴다.
    (platform, post_code) UNIQUE. 이미 저장된 글은 이후 실행에서 건너뛴다.
    '''
    id: Optional[int] = None                     # PK
    run_id: int                                  # FK, 이 글을 판정한 실행(실패 등으로 여러번 실행됐다면 마지막 실행)
    
    author_id: int                               # FK
    platform: Platform
    post_code: str                               # URL의 게시글 코드(Threads·Instagram) 또는 ID(X)
    content: Optional[str] = None
    posted_at: Optional[datetime] = None         # '2일 전' 같은 상대 표기를 UTC로 환산한 값
    like_count: Optional[int] = None             # 판정 시점 값
    
    search_keyword: str                          # 이 글을 찾은 검색어
    status: PostStatus                           # 자동모드: liked·failed | 승인모드: candidate → approved·rejected → liked·failed
    liked_at: Optional[datetime] = None          # 상한·쿨다운 계산 기준
    created_at: Optional[datetime] = None        # 최초 판정 시각
    updated_at: Optional[datetime] = None
