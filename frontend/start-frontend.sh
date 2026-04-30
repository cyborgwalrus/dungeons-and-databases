#!/bin/sh
set -eu

PORT="${PORT}"
BACKEND_API_BASE="${BACKEND_API_BASE:-/api}"

BACKEND_PUBLIC_URL="https://dnd-backend-6ymc.onrender.com"

cat > /usr/share/nginx/html/runtime-config.js <<EOF
window.__API_BASE__ = "${BACKEND_API_BASE}";
EOF

sed \
  -e "s/__PORT__/${PORT}/g" \
  -e "s#__BACKEND_PUBLIC_URL__#${BACKEND_PUBLIC_URL}#g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_API_BASE=${BACKEND_API_BASE}, PORT=${PORT}"
exec nginx -g 'daemon off;'