#!/usr/bin/env bash
# worker 컨테이너 시작: 가상 화면 → 화면 공유(VNC) → 웹 접속(noVNC) → 실행 루프
set -euo pipefail

export DISPLAY=:99
PROFILE_DIR="${BROWSER_PROFILE_DIR:-/data/browser-profile}"

# 비정상 종료로 남은 잠금 파일 정리
rm -f /tmp/.X99-lock "$PROFILE_DIR"/Singleton*

Xvfb :99 -screen 0 1280x900x24 -nolisten tcp &
while [ ! -e /tmp/.X11-unix/X99 ]; do sleep 0.2; done

mkdir -p /tmp/vnc
# VNC는 비밀번호 없이 컨테이너 내부(localhost)에서만 받는다. 외부에서는 front의 /vnc 프록시로만 접속한다
x11vnc -display :99 -nopw -localhost -rfbport 5900 -forever -shared -quiet -bg -o /tmp/vnc/x11vnc.log
websockify --web /usr/share/novnc 6080 localhost:5900 > /tmp/vnc/websockify.log 2>&1 &

exec python -m job.run_worker
