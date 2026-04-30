#!/bin/sh
set -eu



PORT="${PORT}"
BACKEND_PORT="${BACKEND_PORT}"


# trickery needed to make the same script and nginx work for both compose and render cloud
#################################################################
if ! echo "$BACKEND_HOST" | grep -q "\."; then
  FULL_BACKEND_HOST="${BACKEND_HOST}.render.local"
else
  FULL_BACKEND_HOST="${BACKEND_HOST}"
fi

DNS_RESOLVER=$(awk '/nameserver/ {print $2; exit}' /etc/resolv.conf)

if [ -z "$DNS_RESOLVER" ]; then
    DNS_RESOLVER="8.8.8.8"
fi
##############################################################

sed \
  -e "s/__PORT__/${PORT}/g" \
  -e "s/__BACKEND_HOST__/${BACKEND_HOST}/g" \
  -e "s/__BACKEND_PORT__/${BACKEND_PORT}/g" \
  -e "s/__DNS_RESOLVER__/${DNS_RESOLVER}/g" \
  /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "[start-frontend] starting with BACKEND_HOST=${BACKEND_HOST}, BACKEND_PORT=${BACKEND_PORT}, PORT=${PORT}, RESOLVER=${DNS_RESOLVER}"
exec nginx -g 'daemon off;'