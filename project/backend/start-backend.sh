#!/bin/sh
set -e

cd "$(dirname "$0")/.."

echo "[start-backend] starting with FLASK_ENV=${FLASK_ENV}"

if [ "${FLASK_ENV}" = 'development' ]; then
  echo "[start-backend] development mode: deleting existing DB (if any)"
  flask --app backend.app delete-db || true
fi

echo "[start-backend] initializing DB"
flask --app backend.app init-db || true

echo "[start-backend] seeding full loadout"
flask --app backend.app seed-full-loadout || true

echo "[start-backend] launching Flask"
exec flask --app backend.app run --host=0.0.0.0
