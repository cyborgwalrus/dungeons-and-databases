#!/bin/sh
set -eu

RENDER="${RENDER:-false}"
PORT="${PORT:-8080}"
BACKEND_API_BASE="${BACKEND_API_BASE:-/api}"
BACKEND_HOST="${BACKEND_HOST:-backend}"
BACKEND_PORT="${BACKEND_PORT:-10000}"

if [ "${RENDER}" = "true" ]; then
  BACKEND_API_BASE="https://${BACKEND_HOST}.onrender.com/api"
fi

cat > /tmp/runtime-config.js <<EOF
window.__API_BASE__ = "${BACKEND_API_BASE}";
EOF

if [ "${RENDER}" = "true" ]; then
  : > /tmp/api-proxy.locations
else
  sed \
    -e "s/__BACKEND_HOST__/${BACKEND_HOST}/g" \
    -e "s/__BACKEND_PORT__/${BACKEND_PORT}/g" \
    api-proxy.locations.template > /tmp/api-proxy.locations
fi

sed \
  -e "s/__PORT__/${PORT}/g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_API_BASE=${BACKEND_API_BASE}, PORT=${PORT}"
exec nginx -g 'daemon off;'