# ========== 플랫폼 계정 상태 예외 (감지하면 실행을 즉시 멈춘다) ==========



class LoginRequiredError(Exception):
    pass



class ChallengeDetectedError(Exception):
    pass



class ActionBlockedError(Exception):
    pass
