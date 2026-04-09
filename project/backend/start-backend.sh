#!/bin/sh
set -e

echo "[start-backend] starting with FLASK_ENV=${FLASK_ENV}"

if [ "${FLASK_ENV}" = 'development' ]; then
  echo "[start-backend] development mode: deleting existing DB (if any)"
  flask delete-db || true
fi

echo "[start-backend] initializing DB"
flask init-db || true

echo "[start-backend] seeding full loadout"
flask seed-full-loadout || true

echo "[start-backend] launching Flask"
exec flask run --host=0.0.0.0
