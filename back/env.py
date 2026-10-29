import os



# ========== 환경변수 로드 ==========



DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
DB_USER = os.environ.get('DB_USER', 'lbt_user')
DB_PWD = os.environ.get('DB_PWD', '')
DB_NAME = os.environ.get('DB_NAME', 'lbt_db')

# worker 전용
BROWSER_PROFILE_DIR = os.environ.get('BROWSER_PROFILE_DIR', '/data/browser-profile')
HEARTBEAT_FILE = os.environ.get('HEARTBEAT_FILE', '/tmp/worker_heartbeat')
DEBUG_DIR = os.environ.get('DEBUG_DIR', '/app/debug')        # 화면 진단 파일 저장 위치(호스트의 back/debug)
