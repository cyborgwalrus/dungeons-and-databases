#!/bin/sh
set -eu

DNS_RESOLVER=$(awk '/nameserver/ {print $2; exit}' /etc/resolv.conf)

if [ -z "$DNS_RESOLVER" ]; then
    DNS_RESOLVER="8.8.8.8"
fi

PORT="${PORT}"
BACKEND_HOST="${BACKEND_HOST}"
BACKEND_PORT="${BACKEND_PORT}"

sed \
  -e "s/__PORT__/${PORT}/g" \
  -e "s/__BACKEND_HOST__/${BACKEND_HOST}/g" \
  -e "s/__BACKEND_PORT__/${BACKEND_PORT}/g" \
  -e "s/__DNS_RESOLVER__/${DNS_RESOLVER}/g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_HOST=${BACKEND_HOST}, BACKEND_PORT=${BACKEND_PORT}, PORT=${PORT}, RESOLVER=${DNS_RESOLVER}"
exec nginx -g 'daemon off;'