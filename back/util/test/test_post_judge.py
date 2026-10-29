from datetime import datetime, timedelta, timezone

import service.post_service as post_service
import util.client.threads as threads
from database.schema_enum import SkipReason
from util.client.threads import ThreadsPost



# ========== 게시글 판정·파싱 회귀 테스트 (DB 불필요) ==========
# 실행: back 폴더에서 python -m pytest util/test



NOW = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)
TARGETING_SET = {
    'max_post_age_hour': 72,
    'max_like_count': 100,
    'language': 'ko',
    'is_verified_excluded': True,
    'exclude_keyword_list': ['광고', 'AD'],
}



def build_post(**field):
    post_field = {
        'post_code': 'C1',
        'handle': 'kim',
        'content': '전남친 생각나는 밤',
        'posted_at': NOW - timedelta(hours=1),
        'like_count': 3,
    }
    post_field.update(field)
    threads_post = ThreadsPost(**post_field)

    return threads_post



def test_judge_pass():
    assert post_service.judge_post_content(build_post(), TARGETING_SET, NOW) is None



def test_judge_skip_reason():
    case_list = [
        (build_post(is_liked=True), SkipReason.ALREADY_PROCESSED),
        (build_post(content=''), SkipReason.UNREADABLE),
        (build_post(posted_at=None), SkipReason.UNREADABLE),
        (build_post(posted_at=NOW - timedelta(hours=73)), SkipReason.TOO_OLD),
        (build_post(content='I miss my ex'), SkipReason.LANGUAGE),
        (build_post(content='전남친 선물 광고'), SkipReason.EXCLUDE_KEYWORD),
        (build_post(content='전남친 ad 문의'), SkipReason.EXCLUDE_KEYWORD),
        (build_post(like_count=101), SkipReason.LIKE_COUNT),
        (build_post(like_count=None), SkipReason.LIKE_COUNT),
        (build_post(is_verified=True), SkipReason.VERIFIED),
    ]
    for threads_post, skip_reason in case_list:
        assert post_service.judge_post_content(threads_post, TARGETING_SET, NOW) == skip_reason, threads_post



def test_judge_no_limit():
    targeting_set = {**TARGETING_SET, 'max_post_age_hour': None, 'max_like_count': None}
    threads_post = build_post(posted_at=None, like_count=None)
    assert post_service.judge_post_content(threads_post, targeting_set, NOW) is None



def test_language():
    assert post_service.is_language_matched('오늘 헤어졌다 ㅠㅠ', 'ko')
    assert post_service.is_language_matched('元カレのことを思い出す', 'ja')
    assert post_service.is_language_matched('I miss my ex so much', 'en')
    assert not post_service.is_language_matched('I miss my ex so much', 'ko')
    assert not post_service.is_language_matched('😭😭', 'ko')



def test_parse_count():
    case_list = [('', 0), ('7', 7), ('1,234', 1234), ('1.2천', 1200), ('3만', 30000), ('2.5K', 2500), ('1M', 1000000), ('??', None)]
    for count_text, count in case_list:
        assert threads.parse_count(count_text) == count, count_text



def test_build_url():
    assert threads.build_post_url('kim', 'C1') == 'https://www.threads.com/@kim/post/C1'
    assert threads.build_profile_url('kim') == 'https://www.threads.com/@kim'
