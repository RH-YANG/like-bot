from enum import StrEnum



# ========== DB 테이블의 enum성 컬럼 값 목록 ==========



class Platform(StrEnum):
    THREADS = 'threads'
    INSTAGRAM = 'instagram'
    X = 'x'



class RunMode(StrEnum):
    AUTO = 'auto'                                    # 조건을 통과하면 바로 좋아요
    APPROVAL = 'approval'                            # 후보를 모은 뒤 사용자가 승인한 글만 좋아요



class RunStatus(StrEnum):
    PENDING = 'pending'
    RUNNING = 'running'
    AWAITING_APPROVAL = 'awaiting_approval'          # 승인 모드에서 후보 수집을 마치고 승인을 기다리는 중
    STOPPING = 'stopping'                            # 중지 요청을 받아 현재 동작을 마무리하는 중
    FINISHED = 'finished'



class RunEndReason(StrEnum):
    GOAL_REACHED = 'goal_reached'                    # 목표 개수 달성
    SEARCH_EXHAUSTED = 'search_exhausted'            # 검색 결과 소진
    MAX_SCAN_REACHED = 'max_scan_reached'            # 최대 검토 게시글 수 도달
    MAX_DURATION_REACHED = 'max_duration_reached'    # 최대 실행 시간 초과
    LIMIT_REACHED = 'limit_reached'                  # 플랫폼 일간·시간당 상한 도달
    USER_STOPPED = 'user_stopped'                    # 사용자가 중지
    LOGIN_REQUIRED = 'login_required'                # 로그인 풀림
    CHALLENGE_DETECTED = 'challenge_detected'        # 본인 인증·캡차 요구
    ACTION_BLOCKED = 'action_blocked'                # 활동 제한 메시지 감지
    INTERRUPTED = 'interrupted'                      # heartbeat 끊김(PC 절전·컨테이너 종료 등)
    ERROR = 'error'                                  # 그 외 예외



class PostStatus(StrEnum):
    CANDIDATE = 'candidate'                          # 승인 모드: 조건을 통과해 승인을 기다리는 글
    APPROVED = 'approved'                            # 승인됨, 좋아요 대기
    REJECTED = 'rejected'                            # 거절됨, 이후 실행에서도 제외
    LIKED = 'liked'
    FAILED = 'failed'                                # 좋아요 클릭 실패



class SkipReason(StrEnum):
    ALREADY_PROCESSED = 'already_processed'          # 이미 저장된 글(좋아요·후보·거절 등) 또는 플랫폼상 이미 좋아요한 글
    AUTHOR_COOLDOWN = 'author_cooldown'              # 쿨다운 기간 내 같은 작성자
    AUTHOR_BLOCKED = 'author_blocked'                # 수동 제외 계정
    TOO_OLD = 'too_old'                              # 게시 후 경과 시간 초과
    EXCLUDE_KEYWORD = 'exclude_keyword'              # 제외 키워드 포함
    LIKE_COUNT = 'like_count'                        # 좋아요 수 상한 초과
    VERIFIED = 'verified'                            # 인증 배지 계정
    LANGUAGE = 'language'                            # 타겟팅 세트의 대상 언어가 아닌 글
    UNREADABLE = 'unreadable'                        # 게시 시각·본문 파싱 실패
