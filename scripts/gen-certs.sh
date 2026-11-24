#!/usr/bin/env bash
# Делает самоподписанный сертификат для локального HTTPS (если нет mkcert).
# Имена файлов совпадают с теми, что ждёт nginx/nginx.conf.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p cert
if [ -f cert/localhost+2.pem ]; then
  echo "cert/localhost+2.pem уже есть, ничего не делаю"
  exit 0
fi
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout cert/localhost+2-key.pem -out cert/localhost+2.pem \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"
echo "Готово: cert/localhost+2.pem (браузер покажет предупреждение, это нормально)"
