#!/bin/sh
set -e

#THREAD_COUNT="$(nproc --all)"  # Use all available CPU cores for Gunicorn workers
THREAD_COUNT=4  # Use a fixed number of workers for better performance on Render's free tier
BIND_PORT="${PORT:-5000}"

cd "$(dirname "$0")/.."

echo "[start-backend] initializing DB tables"
flask --app backend.app init-db || true

echo "[start-backend] launching Gunicorn, binding to port ${BIND_PORT} with ${THREAD_COUNT} workers"
exec gunicorn --bind 0.0.0.0:"${BIND_PORT}" --workers "${THREAD_COUNT:-4}" backend.app:app
