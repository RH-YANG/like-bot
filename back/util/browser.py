import json
import logging
from datetime import datetime
from pathlib import Path

import env



# ========== worker 브라우저 (로그인 상태를 유지하는 Chromium 프로필) ==========



logger = logging.getLogger('browser')

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 900



def open_browser_context(playwright):
    # 가상 화면(DISPLAY)에 창을 띄워 noVNC로 로그인·진행 상황을 볼 수 있게 한다
    browser_context = playwright.chromium.launch_persistent_context(
        user_data_dir=env.BROWSER_PROFILE_DIR,
        headless=False,
        locale='ko-KR',
        timezone_id='Asia/Seoul',
        no_viewport=True,
        args=[
            '--window-position=0,0',
            f'--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}',
            '--disable-blink-features=AutomationControlled',
        ],
    )

    return browser_context



def get_main_page(browser_context):
    page = None
    if browser_context.pages:
        page = browser_context.pages[0]
    else:
        page = browser_context.new_page()

    return page



def is_page_alive(page):
    is_alive = False
    try:
        page.title()
        is_alive = not page.is_closed()
    except Exception:
        is_alive = False

    return is_alive



# 화면 구조 진단용 요약: 선택자별 개수와 화면에 있는 aria-label 목록
PAGE_SUMMARY_SCRIPT = '''() => {
    const count = (selector) => document.querySelectorAll(selector).length;
    const labelCount = {};
    for (const el of document.querySelectorAll('[aria-label]')) {
        const label = el.getAttribute('aria-label');
        labelCount[label] = (labelCount[label] || 0) + 1;
    }
    const postLinkList = [...document.querySelectorAll('a[href*="/post/"]')].slice(0, 10).map((a) => ({
        href: a.getAttribute('href'),
        text: (a.innerText || '').slice(0, 40),
        childTagList: [...a.children].map((child) => child.tagName.toLowerCase()),
    }));
    return {
        url: location.href,
        title: document.title,
        count: {
            postLink: count('a[href*="/post/"]'),
            time: count('time'),
            timeWithDatetime: count('time[datetime]'),
            postLinkTime: count('a[href*="/post/"] time'),
            pressableContainer: count('[data-pressable-container]'),
            roleButton: count('[role="button"]'),
            spanDirAuto: count('span[dir="auto"]'),
        },
        labelCount,
        postLinkList,
        bodyText: (document.body.innerText || '').slice(0, 1500),
    };
}'''



def save_page_snapshot(page, name):
    # 화면 HTML·스크린샷·구조 요약을 DEBUG_DIR에 남긴다. 같은 name은 덮어쓴다. 진단용이라 실패해도 실행은 계속한다
    debug_dir = Path(env.DEBUG_DIR)
    saved_dir = None
    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
        page_summary = page.evaluate(PAGE_SUMMARY_SCRIPT)
        page_summary['saved_at'] = datetime.now().isoformat()
        (debug_dir / f'{name}.json').write_text(json.dumps(page_summary, ensure_ascii=False, indent=2), encoding='utf-8')
        (debug_dir / f'{name}.html').write_text(page.content(), encoding='utf-8')
        page.screenshot(path=str(debug_dir / f'{name}.png'), full_page=False)
        saved_dir = str(debug_dir)
    except Exception:
        logger.warning('진단 화면(%s)을 저장하지 못했어요.', name, exc_info=True)

    return saved_dir
