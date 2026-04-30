#!/bin/sh
set -eu

PORT="${PORT}"

BACKEND_PUBLIC_URL="https://dnd-backend-6ymc.onrender.com"

sed \
  -e "s/__PORT__/${PORT}/g" \
  -e "s#__BACKEND_PUBLIC_URL__#${BACKEND_PUBLIC_URL}#g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_PUBLIC_URL=${BACKEND_PUBLIC_URL}, PORT=${PORT}"
exec nginx -g 'daemon off;'