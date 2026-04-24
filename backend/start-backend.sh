#!/bin/sh
set -e

THREAD_COUNT="$(nproc --all)"  # Use all available CPU cores for Gunicorn workers

cd "$(dirname "$0")/.."

echo "[start-backend] starting with WIPE_DB_ON_RESTART=${WIPE_DB_ON_RESTART}"

if [ "${WIPE_DB_ON_RESTART}" = 'true' ]; then
  echo "[start-backend] wiping DB on restart"
  flask --app backend.app clear-db || true
fi

echo "[start-backend] initializing DB tables"
flask --app backend.app init-db || true

echo "[start-backend] launching Gunicorn"
exec gunicorn --bind 0.0.0.0:5000 --workers "${THREAD_COUNT:-4}" backend.app:app
