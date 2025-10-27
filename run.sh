#!/usr/bin/env bash
# 一键：若端口有旧进程则杀掉并重启；否则直接启动
PORT="${MAIC_PORT:-8123}"
APP_DIR="/home/lxb/Documents/MAICCONNECTION"
UVICORN="/home/lxb/anaconda3/envs/lxbenv/bin/uvicorn"
LOG_DIR="$APP_DIR/log"

mkdir -p "$LOG_DIR"

# 若端口上已有服务，则先停掉（忽略不存在的情况）
if lsof -tiTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  kill -TERM $(lsof -tiTCP:"$PORT" -sTCP:LISTEN) 2>/dev/null || true
  sleep 1
fi

cd "$APP_DIR"
nohup "$UVICORN" main:app --host 0.0.0.0 --port "$PORT" --workers 1 --log-level info >> "$LOG_DIR/service.out" 2>&1 &
echo "OK: PID $! on :$PORT  (logs -> $LOG_DIR/service.out)"
