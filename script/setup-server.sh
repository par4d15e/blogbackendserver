#!/bin/bash
set -euo pipefail

# 清理函数
cleanup() {
    for pid in "$CELERY_WORKER_PID" "$CELERY_BEAT_PID" "$FASTAPI_PID"; do
        [ ! -z "${pid:-}" ] && kill -0 "$pid" 2>/dev/null && kill -TERM "$pid" && wait "$pid" 2>/dev/null || true
    done
    exit 0
}

trap cleanup SIGTERM SIGINT

# 检查环境配置文件
ENV=${ENV:-production}
[ ! -f "/server/secret/.env.$ENV" ] && { echo "❌ Environment file not found: /server/secret/.env.$ENV"; exit 1; }

# 查找命令路径（优先全局，其次 /server/.venv/bin）
find_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        command -v "$1"
    elif [ -x "/server/.venv/bin/$1" ]; then
        echo "/server/.venv/bin/$1"
    else
        return 1
    fi
}

# 检查必要的命令
UVICORN_CMD=$(find_cmd uvicorn) || { echo "❌ uvicorn not found"; exit 1; }
CELERY_CMD=$(find_cmd celery) || { echo "❌ celery not found"; exit 1; }

# 切换到应用目录
cd /server || { echo "❌ Cannot cd to /server"; exit 1; }

# 启动 FastAPI
echo "🚀 Starting FastAPI..."
"$UVICORN_CMD" app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}" &
FAST API_PID=$!
sleep 2
kill -0 "$FASTAPI_PID" 2>/dev/null || { echo "❌ FastAPI failed to start"; exit 1; }
echo "✅ FastAPI started (PID: $FASTAPI_PID)"

# 准备 Celery 环境（使用非 root 用户以提高安全性）
CELERY_UID=$(id -u appuser 2>/dev/null || echo "1000")
CELERY_GID=$(id -g appuser 2>/dev/null || echo "1000")
mkdir -p /server/.celery
chown -R "$CELERY_UID:$CELERY_GID" /server/.celery 2>/dev/null || true
chmod o+w /server 2>/dev/null || true

# 启动 Celery Worker
echo "🚀 Starting Celery Worker..."
"$CELERY_CMD" -A app.core.celery.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --uid="$CELERY_UID" \
    --gid="$CELERY_GID" &
CELERY_WORKER_PID=$!
sleep 2
kill -0 "$CELERY_WORKER_PID" 2>/dev/null || { echo "❌ Celery Worker failed to start"; cleanup; exit 1; }
echo "✅ Celery Worker started (PID: $CELERY_WORKER_PID)"

# 启动 Celery Beat
echo "🚀 Starting Celery Beat..."
"$CELERY_CMD" -A app.core.celery.celery_app beat \
    --loglevel=info \
    --uid="$CELERY_UID" \
    --gid="$CELERY_GID" &
CELERY_BEAT_PID=$!
sleep 2
kill -0 "$CELERY_BEAT_PID" 2>/dev/null || { echo "❌ Celery Beat failed to start"; cleanup; exit 1; }
echo "✅ Celery Beat started (PID: $CELERY_BEAT_PID)"

echo "✅ All services started successfully"
echo "   - FastAPI: PID $FASTAPI_PID"
echo "   - Celery Worker: PID $CELERY_WORKER_PID"
echo "   - Celery Beat: PID $CELERY_BEAT_PID"

# 等待子进程
wait
