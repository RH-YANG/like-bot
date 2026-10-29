from dataclasses import dataclass

from database.schema_enum import Platform



# ========== 플랫폼별 안전 상한과 실행 속도 ==========



@dataclass(frozen=True)
class PlatformConfig:
    daily_like_limit: int            # 최근 24시간 좋아요 상한
    hourly_like_limit: int           # 최근 1시간 좋아요 상한
    min_interval_sec: int            # 좋아요 사이 최소 대기(초)
    max_interval_sec: int            # 좋아요 사이 최대 대기(초)



THREADS_CONFIG = PlatformConfig(
    daily_like_limit=100,
    hourly_like_limit=30,
    min_interval_sec=40,
    max_interval_sec=180,
)


# 등록되지 않은 플랫폼은 지원하지 않는 것으로 취급한다
PLATFORM_CONFIG = {
    Platform.THREADS: THREADS_CONFIG,
}
