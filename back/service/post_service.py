from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import database.dao.post_dao as post_dao
import database.dao.author_dao as author_dao
import util.client.threads as threads
from config.platform import PLATFORM_CONFIG
from database.dbms_control import connect_db
from database.schema import Author, Post
from database.schema_enum import Platform, PostStatus, SkipReason
from database.dto import PostResponse, LikeUsageResponse



# ========== 게시글 판정·저장·조회 ==========



SECOND_PER_HOUR = 3_600
SECOND_PER_DAY = 86_400
POST_LIST_LIMIT = 200
POST_URL_BUILDER = {
    Platform.THREADS: threads.build_post_url,
}
PROFILE_URL_BUILDER = {
    Platform.THREADS: threads.build_profile_url,
}
# 언어 판정: 글자 중 해당 문자 비율이 기준 이상이면 같은 언어로 본다
LANGUAGE_RATIO = {
    'ko': 0.3,
    'ja': 0.2,
    'en': 0.7,
}



def build_post_url(platform, handle, post_code):
    # → 플랫폼별 게시글 주소를 만든다
    post_url = POST_URL_BUILDER[platform](handle, post_code)

    return post_url



def build_profile_url(platform, handle):
    # → 플랫폼별 프로필 주소를 만든다
    profile_url = PROFILE_URL_BUILDER[platform](handle)

    return profile_url



def count_script_char(content):
    # → 글자를 문자 체계별로 센다
    char_count = {'letter': 0, 'ko': 0, 'ja': 0, 'en': 0}
    for char in content:
        if not char.isalpha():
            continue
        char_count['letter'] += 1
        if '가' <= char <= '힣' or 'ㄱ' <= char <= 'ㆎ':
            char_count['ko'] += 1
        elif '぀' <= char <= 'ヿ':
            char_count['ja'] += 1
        elif char.isascii():
            char_count['en'] += 1

    return char_count



def is_language_matched(content, language):
    # → 본문이 대상 언어로 쓰였는지 판정한다
    char_count = count_script_char(content)

    is_matched = False
    if char_count['letter'] > 0:
        is_matched = char_count[language] / char_count['letter'] >= LANGUAGE_RATIO[language]

    return is_matched



def judge_post_content(threads_post, targeting_set, now):
    # → DB 없이 판정할 수 있는 조건을 검사한다. 통과하면 None
    content = threads_post.content or ''
    max_post_age_hour = targeting_set['max_post_age_hour']
    max_like_count = targeting_set['max_like_count']
    exclude_keyword_list = [k.lower() for k in targeting_set['exclude_keyword_list']]

    skip_reason = None
    if threads_post.is_liked:
        skip_reason = SkipReason.ALREADY_PROCESSED
    elif not content.strip() or (max_post_age_hour is not None and threads_post.posted_at is None):
        skip_reason = SkipReason.UNREADABLE
    elif max_post_age_hour is not None and threads_post.posted_at < now - timedelta(hours=max_post_age_hour):
        skip_reason = SkipReason.TOO_OLD
    elif not is_language_matched(content, targeting_set['language']):
        skip_reason = SkipReason.LANGUAGE
    elif any(keyword in content.lower() for keyword in exclude_keyword_list):
        skip_reason = SkipReason.EXCLUDE_KEYWORD
    elif max_like_count is not None and (threads_post.like_count is None or threads_post.like_count > max_like_count):
        skip_reason = SkipReason.LIKE_COUNT
    elif targeting_set['is_verified_excluded'] and threads_post.is_verified:
        skip_reason = SkipReason.VERIFIED

    return skip_reason



@connect_db
def judge_post(conn, cur, platform, threads_post, targeting_set):
    # → 게시글이 좋아요 대상인지 판정한다. 대상이면 None, 아니면 건너뛸 이유
    # 1. 본문·시각·언어 등 화면 정보만으로 판정
    now = datetime.now(timezone.utc)
    skip_reason = judge_post_content(threads_post, targeting_set, now)
    if skip_reason is not None:
        return skip_reason

    # 2. 이미 저장된 글(좋아요·후보·거절·실패)
    post = post_dao.select_by_code(cur, platform, threads_post.post_code)
    if post is not None:
        skip_reason = SkipReason.ALREADY_PROCESSED
        return skip_reason

    # 3. 작성자 제외·쿨다운
    author = author_dao.select_by_handle(cur, platform, threads_post.handle)
    if author is not None:
        cooldown_second = targeting_set['author_cooldown_day'] * SECOND_PER_DAY
        recent_post_count = post_dao.count_author_recent(cur, author.id, cooldown_second)
        if author.is_blocked:
            skip_reason = SkipReason.AUTHOR_BLOCKED
        elif recent_post_count > 0:
            skip_reason = SkipReason.AUTHOR_COOLDOWN

    return skip_reason



@connect_db
def save_post(conn, cur, run_id, platform, threads_post, search_keyword, post_status):
    # → 작성자를 갱신하고 판정한 게시글을 저장한다
    author = Author(
        platform=platform,
        handle=threads_post.handle,
        display_name=threads_post.display_name,
        is_verified=threads_post.is_verified,
    )
    author_id = author_dao.upsert(cur, author)

    post = Post(
        run_id=run_id,
        author_id=author_id,
        platform=platform,
        post_code=threads_post.post_code,
        content=threads_post.content,
        posted_at=threads_post.posted_at,
        like_count=threads_post.like_count,
        search_keyword=search_keyword,
        status=post_status,
    )
    post_id = post_dao.insert(cur, post)

    conn.commit()

    return post_id



@connect_db
def mark_post_result(conn, cur, post_id, is_liked):
    # → 승인(좋아요 대기) 상태의 글을 클릭 결과에 따라 liked 또는 failed로 바꾼다
    to_status = PostStatus.FAILED
    if is_liked:
        to_status = PostStatus.LIKED

    post_dao.update_status(cur, post_id, [PostStatus.APPROVED], to_status)

    conn.commit()



def count_recent_like(cur, platform):
    # → 최근 24시간·1시간 좋아요 수
    daily_liked_count = post_dao.count_liked_since(cur, platform, SECOND_PER_DAY)
    hourly_liked_count = post_dao.count_liked_since(cur, platform, SECOND_PER_HOUR)

    return daily_liked_count, hourly_liked_count



@connect_db
def select_recent_like_count(conn, cur, platform):
    # → 일간·시간당 상한 확인용 최근 좋아요 수 (daily, hourly)
    daily_liked_count, hourly_liked_count = count_recent_like(cur, platform)

    return daily_liked_count, hourly_liked_count



@connect_db
def select_approved_post_row_list(conn, cur, run_id):
    # → 승인 모드에서 좋아요를 기다리는 글 목록(작성자 아이디 포함)
    post_row_list = post_dao.select_by_run_status(cur, run_id, PostStatus.APPROVED)

    return post_row_list



def build_post_response(post_row):
    # → 게시글·작성자 조회 결과를 응답 모델로 바꾼다
    post_url = build_post_url(post_row['platform'], post_row['author_handle'], post_row['post_code'])
    post_response = PostResponse(**post_row, url=post_url)

    return post_response



def select_post_response_list(cur, run_id, status_list, limit):
    # → 조건에 맞는 게시글을 응답 모델 목록으로 조회한다
    post_row_list = post_dao.select_with_author(cur, run_id, status_list, limit)
    post_response_list = [build_post_response(post_row) for post_row in post_row_list]

    return post_response_list



@connect_db
def select_post_list(conn, cur, status_list):
    # → 게시글 훑어보기 목록. status_list가 None이면 전체 상태
    post_response_list = select_post_response_list(cur, None, status_list, POST_LIST_LIMIT)

    return post_response_list



@connect_db
def select_like_usage_list(conn, cur):
    # → 플랫폼별 좋아요 상한(config/platform.py)과 최근 24시간·1시간 좋아요 수
    like_usage_list = []
    for platform, platform_config in PLATFORM_CONFIG.items():
        daily_liked_count, hourly_liked_count = count_recent_like(cur, platform)
        platform_config_field = asdict(platform_config)
        like_usage = LikeUsageResponse(
            **platform_config_field,
            platform=platform,
            daily_liked_count=daily_liked_count,
            hourly_liked_count=hourly_liked_count,
        )
        like_usage_list.append(like_usage)

    return like_usage_list
