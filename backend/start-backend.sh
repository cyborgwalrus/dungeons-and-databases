#!/bin/sh
set -e

cd "$(dirname "$0")/.."

echo "[start-backend] starting with WIPE_DB_ON_RESTART=${WIPE_DB_ON_RESTART}"

if [ "${WIPE_DB_ON_RESTART}" = 'true' ]; then
  echo "[start-backend] wiping DB on restart"
  flask --app backend.app delete-db || true
fi

echo "[start-backend] initializing DB"
flask --app backend.app init-db || true

echo "[start-backend] launching Flask"
exec flask --app backend.app run --host=0.0.0.0 --reload
