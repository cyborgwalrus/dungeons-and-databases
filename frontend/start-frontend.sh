#!/bin/sh
set -eu

PORT="${PORT}"
BACKEND_API_BASE="${BACKEND_API_BASE:-http://localhost:10000/api}"

cat > /tmp/runtime-config.js <<EOF
window.__API_BASE__ = "${BACKEND_API_BASE}";
EOF

sed \
  -e "s/__PORT__/${PORT}/g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_API_BASE=${BACKEND_API_BASE}, PORT=${PORT}"
exec nginx -g 'daemon off;'