#!/bin/sh
set -eu

PORT="${PORT}"
BACKEND_HOST="${BACKEND_HOST}"
BACKEND_PORT="${BACKEND_PORT}"
BACKEND_API_BASE="${BACKEND_API_BASE:-/api}"

cat > /usr/share/nginx/html/runtime-config.js <<EOF
window.__API_BASE__ = "${BACKEND_API_BASE}";
EOF

sed \
  -e "s/__PORT__/${PORT}/g" \
  -e "s/__BACKEND_HOST__/${BACKEND_HOST}/g" \
  -e "s/__BACKEND_PORT__/${BACKEND_PORT}/g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_HOST=${BACKEND_HOST}, BACKEND_PORT=${BACKEND_PORT}, PORT=${PORT}"
exec nginx -g 'daemon off;'