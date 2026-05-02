#!/bin/sh
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  db_host="$(printf '%s' "$DATABASE_URL" | sed -n 's#^[^:]*://[^@]*@\([^:/?#]*\).*$#\1#p')"
  export ADMINER_DEFAULT_SERVER="$db_host"
fi

exec php -S "0.0.0.0:${PORT:-8080}" -t /var/www/html