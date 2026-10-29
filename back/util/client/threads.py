import logging
import random
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote
from pydantic import BaseModel

from util.browser import save_page_snapshot
from util.handler.platform_exception import LoginRequiredError, ChallengeDetectedError, ActionBlockedError



# ========== Threads 웹 화면 자동화 (Playwright) ==========
# 공개 API로는 다른 사람 글에 좋아요를 누를 수 없어 로그인된 브라우저 화면을 조작한다.
# Threads 화면 구조가 바뀌면 아래 라벨과 POST_SCRIPT의 선택자를 먼저 확인한다.



logger = logging.getLogger('threads')

THREADS_URL = 'https://www.threads.com'
LABEL = {
    'like': ['좋아요', 'Like'],
    'unlike': ['좋아요 취소', 'Unlike'],
    'verified': ['인증됨', 'Verified'],
}
BLOCK_PHRASE_LIST = ['나중에 다시 시도', 'Try Again Later', '활동이 제한', '제한되었습니다', 'restrict certain activity']
CHALLENGE_URL_PART_LIST = ['/challenge', '/checkpoint', '/accounts/suspended', '/accounts/disabled']
NAVIGATION_TIMEOUT_MS = 30000
PAGE_SETTLE_SEC = (2.0, 4.0)
SCROLL_PAUSE_SEC = (1.5, 3.5)
SCROLL_DISTANCE_PX = (900, 1600)
LIKE_CONFIRM_SEC = (1.5, 2.5)
MAX_EMPTY_SCROLL = 4

# 게시글 영역 탐색 공통 함수. 게시 시각(<time>)을 감싼 링크가 게시글 고유 주소(/@handle/post/code)다.
POST_SCRIPT_LIB = '''
// 아이콘 이름은 aria-label 또는 <svg> 안의 <title>에 있다
const getSvgLabel = (svg) => svg.getAttribute('aria-label') || svg.querySelector('title')?.textContent || '';
const findSvgByLabel = (el, labelList) => [...el.querySelectorAll('svg')].find((svg) => labelList.includes(getSvgLabel(svg))) || null;
const findLikeSvg = (el, label) => findSvgByLabel(el, [...label.like, ...label.unlike]);
const findPostList = (label) => {
    const postList = [];
    const seen = new Set();
    for (const time of document.querySelectorAll('a[href*="/post/"] time[datetime]')) {
        const link = time.closest('a');
        const match = (link.getAttribute('href') || '').match(/\\/@([^/]+)\\/post\\/([^/?#]+)/);
        if (!match || seen.has(match[2])) continue;
        let container = link.closest('[data-pressable-container="true"]');
        if (!container) {
            container = link.parentElement;
            while (container && !findLikeSvg(container, label)) container = container.parentElement;
        }
        // 좋아요 버튼이 없는 영역(인용된 글 등)은 건너뛴다
        if (!container || !findLikeSvg(container, label)) continue;
        // 인용된 글의 시각은 건너뛴다
        if (container.querySelector('a[href*="/post/"] time[datetime]') !== time) continue;
        seen.add(match[2]);
        postList.push({ handle: decodeURIComponent(match[1]), postCode: match[2], time, container });
    }
    return postList;
};
'''
EXTRACT_POST_SCRIPT = '(label) => {' + POST_SCRIPT_LIB + '''
    return findPostList(label).map(({ handle, postCode, time, container }) => {
        const likeSvg = findLikeSvg(container, label);
        const likeButton = likeSvg ? (likeSvg.closest('[role="button"]') || likeSvg.parentElement) : null;
        const textList = [];
        for (const span of container.querySelectorAll('span[dir="auto"]')) {
            if (span.closest('a') || span.closest('[role="button"]') || span.querySelector('time')) continue;
            // 인용된 글(안쪽 게시글 영역)의 본문은 제외한다
            const innerContainer = span.closest('[data-pressable-container="true"]');
            if (innerContainer && innerContainer !== container) continue;
            if (span.parentElement && span.parentElement.closest('span[dir="auto"]')) continue;
            const text = (span.innerText || '').trim();
            if (text) textList.push(text);
        }
        return {
            handle,
            postCode,
            content: textList.join('\\n'),
            postedAt: time.getAttribute('datetime'),
            likeCountText: likeButton ? (likeButton.innerText || '').trim() : '',
            isLiked: !!likeSvg && label.unlike.includes(getSvgLabel(likeSvg)),
            isVerified: !!findSvgByLabel(container, label.verified),
        };
    });
}'''
MARK_LIKE_BUTTON_SCRIPT = '([postCode, label]) => {' + POST_SCRIPT_LIB + '''
    const post = findPostList(label).find((item) => item.postCode === postCode);
    if (!post) return null;
    const likeSvg = findLikeSvg(post.container, label);
    if (!likeSvg) return null;
    const likeButton = likeSvg.closest('[role="button"]') || likeSvg.parentElement;
    likeButton.setAttribute('data-lbt-target', postCode);
    return { label: getSvgLabel(likeSvg), countText: (likeButton.innerText || '').trim() };
}'''



class ThreadsPost(BaseModel):
    post_code: str
    handle: str
    display_name: Optional[str] = None
    content: Optional[str] = None
    posted_at: Optional[datetime] = None
    like_count: Optional[int] = None
    is_liked: bool = False
    is_verified: bool = False



def build_post_url(handle, post_code):
    post_url = f'{THREADS_URL}/@{handle}/post/{post_code}'

    return post_url



def build_profile_url(handle):
    profile_url = f'{THREADS_URL}/@{handle}'

    return profile_url



def build_search_url(keyword):
    # filter=recent: 최근 게시글 탭
    search_url = f'{THREADS_URL}/search?q={quote(keyword)}&serp_type=default&filter=recent'

    return search_url



def parse_count(count_text):
    # '12', '1,234', '1.2천', '3만', '1.2K', '3M' → 정수. 표시가 없으면 0, 해석할 수 없으면 None
    text = (count_text or '').strip().replace(',', '')
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(천|만|K|k|M|m)?', text)

    count = None
    if text == '':
        count = 0
    elif match is not None:
        unit = {'천': 1_000, '만': 10_000, 'K': 1_000, 'k': 1_000, 'M': 1_000_000, 'm': 1_000_000}.get(match.group(2), 1)
        count = int(float(match.group(1)) * unit)

    return count



def parse_posted_at(posted_at_text):
    posted_at = None
    try:
        posted_at = datetime.fromisoformat(posted_at_text)
    except (TypeError, ValueError):
        posted_at = None
    if posted_at is not None and posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    return posted_at



def build_threads_post(raw_post):
    threads_post = ThreadsPost(
        post_code=raw_post['postCode'],
        handle=raw_post['handle'],
        content=raw_post.get('content') or None,
        posted_at=parse_posted_at(raw_post.get('postedAt')),
        like_count=parse_count(raw_post.get('likeCountText')),
        is_liked=bool(raw_post.get('isLiked')),
        is_verified=bool(raw_post.get('isVerified')),
    )

    return threads_post



class ThreadsClient:
    def __init__(self, page):
        self.page = page



    def pause(self, second_range):
        self.page.wait_for_timeout(random.uniform(*second_range) * 1000)



    def goto(self, url):
        self.page.goto(url, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT_MS)
        self.pause(PAGE_SETTLE_SEC)
        self.check_risk()



    def check_risk(self):
        # 본인 인증 화면이나 활동 제한 안내가 보이면 예외를 던진다
        current_url = self.page.url
        if any(part in current_url for part in CHALLENGE_URL_PART_LIST):
            raise ChallengeDetectedError(current_url)

        dialog_text = '\n'.join(self.page.locator('[role="dialog"]').all_inner_texts())
        if any(phrase in dialog_text for phrase in BLOCK_PHRASE_LIST):
            raise ActionBlockedError(dialog_text[:300])



    def check_login(self):
        # 홈 화면에 로그인 링크가 보이면 로그인이 풀린 상태다
        self.goto(THREADS_URL)
        is_login_page = '/login' in self.page.url
        login_link_count = self.page.locator('a[href*="/login"]').count()
        if is_login_page or login_link_count > 0:
            raise LoginRequiredError(self.page.url)



    def open_home(self):
        self.page.goto(THREADS_URL, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT_MS)



    def search(self, keyword):
        # 최근 게시글 검색 결과를 스크롤하며 새로 보이는 글을 하나씩 돌려준다
        self.goto(build_search_url(keyword))

        seen_post_code = set()
        empty_scroll_count = 0
        is_snapshot_saved = False
        while empty_scroll_count < MAX_EMPTY_SCROLL:
            raw_post_list = self.page.evaluate(EXTRACT_POST_SCRIPT, LABEL)
            new_raw_post_list = [p for p in raw_post_list if p['postCode'] not in seen_post_code]
            empty_scroll_count = empty_scroll_count + 1 if not new_raw_post_list else 0
            logger.info('search %r: 화면 게시글 %s개, 새 게시글 %s개', keyword, len(raw_post_list), len(new_raw_post_list))

            # 첫 화면부터 게시글을 하나도 못 읽으면 진단용으로 화면을 저장한다
            if not seen_post_code and not new_raw_post_list and not is_snapshot_saved:
                saved_dir = save_page_snapshot(self.page, 'search_empty')
                is_snapshot_saved = True
                logger.warning('search %r: 게시글을 읽지 못해 화면을 저장했어요: %s', keyword, saved_dir)

            for raw_post in new_raw_post_list:
                seen_post_code.add(raw_post['postCode'])
                threads_post = build_threads_post(raw_post)
                yield threads_post

            self.page.mouse.wheel(0, random.randint(*SCROLL_DISTANCE_PX))
            self.pause(SCROLL_PAUSE_SEC)
            self.check_risk()



    def like_in_page(self, post_code):
        # 현재 화면에 있는 게시글의 좋아요를 누르고 반영됐는지 확인한다
        before_button = self.page.evaluate(MARK_LIKE_BUTTON_SCRIPT, [post_code, LABEL])
        if before_button is None:
            return False
        if before_button['label'] in LABEL['unlike']:
            return True

        like_button = self.page.locator(f'[data-lbt-target="{post_code}"]').first
        like_button.scroll_into_view_if_needed()
        like_button.click()
        self.pause(LIKE_CONFIRM_SEC)
        self.check_risk()

        # 아이콘 이름이 '좋아요 취소'로 바뀌었거나 좋아요 수가 늘었으면 반영된 것으로 본다
        after_button = self.page.evaluate(MARK_LIKE_BUTTON_SCRIPT, [post_code, LABEL]) or {'label': '', 'countText': ''}
        before_count = parse_count(before_button['countText'])
        after_count = parse_count(after_button['countText'])
        is_count_increased = before_count is not None and after_count is not None and after_count > before_count
        is_liked = after_button['label'] in LABEL['unlike'] or is_count_increased

        return is_liked



    def like_post(self, handle, post_code):
        # 게시글 페이지로 이동해 좋아요를 누른다. 삭제·비공개 글이면 게시글을 찾지 못해 False
        self.goto(build_post_url(handle, post_code))
        is_liked = self.like_in_page(post_code)

        return is_liked
