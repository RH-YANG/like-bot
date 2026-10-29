import type { Language } from '../type/targetingSetType'
import type { RunEndReason, RunMode, RunStatus } from '../type/runType'
import type { PostStatus } from '../type/postType'



// worker 브라우저 화면(noVNC). Vite가 /vnc를 worker로 프록시하므로 웹소켓 경로도 vnc/websockify로 준다
export const BROWSER_VIEW_URL = '/vnc/vnc.html?autoconnect=1&reconnect=1&resize=scale&path=vnc/websockify'
export const POLLING_INTERVAL_MS = 3000
export const LIKE_USAGE_POLLING_INTERVAL_MS = 15000


export const RUN_MODE_LABEL: Record<RunMode, string> = {
  auto: '자동',
  approval: '승인 후 좋아요',
}


export const RUN_STATUS_LABEL: Record<RunStatus, string> = {
  pending: '대기',
  running: '실행 중',
  awaiting_approval: '승인 대기',
  stopping: '중지 중',
  finished: '종료',
}


export const RUN_END_REASON_LABEL: Record<RunEndReason, string> = {
  goal_reached: '목표 달성',
  search_exhausted: '검색 결과 소진',
  max_scan_reached: '최대 검토 수 도달',
  max_duration_reached: '최대 실행 시간 초과',
  limit_reached: '좋아요 상한 도달',
  none_approved: '승인한 글 없음',
  user_stopped: '사용자 중지',
  login_required: '로그인 필요',
  challenge_detected: '본인 인증 요구',
  action_blocked: '활동 제한 감지',
  interrupted: '중단됨',
  error: '오류',
}


export const SKIP_REASON_LABEL: Record<string, string> = {
  already_processed: '이미 처리한 글',
  author_cooldown: '작성자 쿨다운',
  author_blocked: '제외 계정',
  too_old: '오래된 글',
  exclude_keyword: '제외 키워드',
  like_count: '좋아요 수 초과',
  verified: '인증 계정',
  language: '대상 언어 아님',
  unreadable: '읽기 실패',
}


export const POST_STATUS_LABEL: Record<PostStatus, string> = {
  candidate: '후보',
  approved: '승인',
  rejected: '거절',
  liked: '좋아요',
  failed: '실패',
}


export const LANGUAGE_LABEL: Record<Language, string> = {
  ko: '한국어',
  ja: '일본어',
  en: '영어',
}
