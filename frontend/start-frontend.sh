#!/bin/sh
set -eu

PORT="${PORT}"

BACKEND_HOST="${BACKEND_HOST}"
BACKEND_PORT="${BACKEND_PORT}"

sed \
  -e "s/__PORT__/${PORT}/g" \
  -e "s/__BACKEND_HOST__/${BACKEND_HOST}/g" \
  -e "s/__BACKEND_PORT__/${BACKEND_PORT}/g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_HOST=${BACKEND_HOST}, BACKEND_PORT=${BACKEND_PORT}, PORT=${PORT}"
exec nginx -g 'daemon off;'