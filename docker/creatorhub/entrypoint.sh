#!/usr/bin/env bash
set -euo pipefail

mkdir -p /tmp/nginx_client_body_temp /tmp/nginx_proxy_temp
Xvfb :99 -screen 0 1365x900x24 -nolisten tcp >/dev/null 2>&1 &
xvfb_pid=$!
export DISPLAY=:99

for _ in $(seq 1 40); do
  if xdpyinfo -display :99 >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

x11vnc -display :99 -forever -shared -nopw -listen 0.0.0.0 \
  -rfbport 5900 -noxdamage >/dev/null 2>&1 &
vnc_pid=$!

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!

nginx -g 'daemon off;' &
nginx_pid=$!

cleanup() {
  kill -TERM "$nginx_pid" "$api_pid" "$vnc_pid" "$xvfb_pid" 2>/dev/null || true
  wait "$nginx_pid" "$api_pid" "$vnc_pid" "$xvfb_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait -n "$nginx_pid" "$api_pid" "$vnc_pid" "$xvfb_pid"
