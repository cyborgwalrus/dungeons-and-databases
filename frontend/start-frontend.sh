#!/bin/sh
set -eu



PORT="${PORT}"
BACKEND_PORT="${BACKEND_PORT}"
BACKEND_HOST="${BACKEND_HOST}"

# needed for dns to work both locally and on Render
DNS_RESOLVER=$(awk '/nameserver/ {print $2; exit}' /etc/resolv.conf)
if [ -z "$DNS_RESOLVER" ]; then
    DNS_RESOLVER="8.8.8.8"
fi

if [ "${RENDER:-}" = "true" ]; then
    echo "[start-frontend] Render environment detected. Using public proxy template."
    BACKEND_URL="${BACKEND_URL:-"${BACKEND_HOST}.onrender.com"}"
    TEMPLATE_FILE="/etc/nginx/templates/render.conf.template"
else
    echo "[start-frontend] Local environment detected. Using internal proxy template."
    BACKEND_URL="${BACKEND_URL:-"http://${BACKEND_HOST}:${BACKEND_PORT}"}"
    TEMPLATE_FILE="/etc/nginx/templates/nginx.conf.template"
fi

sed \
  -e "s|__PORT__|${PORT}|g" \
  -e "s|__BACKEND_URL__|${BACKEND_URL}|g" \
  -e "s|__DNS_RESOLVER__|${DNS_RESOLVER}|g" \
  "$TEMPLATE_FILE" > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_URL=${BACKEND_URL}, PORT=${PORT}, RESOLVER=${DNS_RESOLVER}"
exec nginx -g 'daemon off;'