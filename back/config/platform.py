from dataclasses import dataclass

from database.schema_enum import Platform



# ========== 플랫폼별 안전 상한과 실행 속도 ==========



@dataclass(frozen=True)
class PlatformConfig:
    is_enabled: bool                 # false면 해당 플랫폼 실행 불가
    daily_like_limit: int            # 최근 24시간 좋아요 상한
    hourly_like_limit: int           # 최근 1시간 좋아요 상한
    min_interval_sec: int            # 좋아요 사이 최소 대기(초)
    max_interval_sec: int            # 좋아요 사이 최대 대기(초)
    author_cooldown_day: int         # 같은 작성자에게 다시 좋아요하기까지 최소 일수
    max_run_minute: int              # 실행 1회 최대 시간(분)



THREADS_CONFIG = PlatformConfig(
    is_enabled=True,
    daily_like_limit=100,
    hourly_like_limit=30,
    min_interval_sec=40,
    max_interval_sec=180,
    author_cooldown_day=14,
    max_run_minute=150,
)


# 등록되지 않은 플랫폼은 지원하지 않는 것으로 취급한다
PLATFORM_CONFIG = {
    Platform.THREADS: THREADS_CONFIG,
}
