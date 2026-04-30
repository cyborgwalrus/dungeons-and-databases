#!/bin/sh
set -e

#THREAD_COUNT="$(nproc --all)"  # Use all available CPU cores for Gunicorn workers
THREAD_COUNT=4  # Use a fixed number of workers for better performance on Render's free tier
BIND_PORT="${PORT:-10000}"

cd "$(dirname "$0")/.."

echo "[start-backend] starting with WIPE_DB_ON_RESTART=${WIPE_DB_ON_RESTART}"

if [ "${WIPE_DB_ON_RESTART}" = 'true' ]; then
  echo "[start-backend] wiping DB on restart"
  flask --app backend.app clear-db || true
fi

echo "[start-backend] initializing DB tables"
flask --app backend.app init-db || true

echo "[start-backend] launching Gunicorn, binding to port ${BIND_PORT} with ${THREAD_COUNT} workers"
exec gunicorn --bind 0.0.0.0:"${BIND_PORT}" --workers "${THREAD_COUNT:-4}" backend.app:app
