import logging
import signal
import sys
import time
from playwright.sync_api import sync_playwright

import service.run_service as run_service
import job.like_job as like_job
from database.schema_enum import RunEndReason
from util.browser import open_browser_context, get_main_page, is_page_alive
from util.client.threads import ThreadsClient



# ========== worker 진입점: pending 실행을 하나씩 가져와 처리한다 ==========



logger = logging.getLogger('run_worker')

POLL_SEC = 3



def handle_sigterm(signal_number, frame):
    # docker stop 시 진행 중 실행을 interrupted로 정리할 수 있게 예외로 바꾼다
    raise SystemExit(0)



def open_browser(playwright, browser_context):
    # → 브라우저를 (다시) 열고 Threads 홈을 띄운다. noVNC에서 이 창으로 로그인한다
    if browser_context is not None:
        try:
            browser_context.close()
        except Exception:
            logger.warning('이전 브라우저를 닫지 못했어요.')

    new_browser_context = open_browser_context(playwright)
    page = get_main_page(new_browser_context)
    try:
        ThreadsClient(page).open_home()
    except Exception:
        # 네트워크 문제 등으로 홈을 못 열어도 실행 루프는 계속한다. 실행 시작 때 다시 접속한다
        logger.warning('Threads 홈을 열지 못했어요.', exc_info=True)
    logger.info('브라우저를 열었어요.')

    return new_browser_context, page



def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s', stream=sys.stdout)
    signal.signal(signal.SIGTERM, handle_sigterm)

    recovered_run_id_list = run_service.recover_interrupted_run()
    if recovered_run_id_list:
        logger.info('중단된 실행을 정리했어요: %s', recovered_run_id_list)

    with sync_playwright() as playwright:
        browser_context = None
        page = None
        while True:
            like_job.touch_heartbeat_file()

            # 1. noVNC에서 창을 닫았거나 브라우저가 죽었으면 다시 연다
            if page is None or not is_page_alive(page):
                browser_context, page = open_browser(playwright, browser_context)

            # 2. 대기 중인 실행 처리
            run = run_service.claim_pending_run()
            if run is None:
                time.sleep(POLL_SEC)
                continue

            try:
                like_job.execute_run(run, ThreadsClient(page))
            except SystemExit:
                run_service.finish_run(run.id, RunEndReason.INTERRUPTED)
                raise



if __name__ == '__main__':
    main()
