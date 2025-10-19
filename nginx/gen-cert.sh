#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="nginx/certs"
mkdir -p "$CERT_DIR"

CERT_PATH="$CERT_DIR/localhost.crt"
KEY_PATH="$CERT_DIR/localhost.key"

if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_PATH" \
    -out "$CERT_PATH" \
    -subj "/C=AU/ST=VIC/L=Melbourne/O=Dev/OU=Local/CN=localhost"
  echo "Generated $CERT_PATH and $(basename "$KEY_PATH")"
else
  echo "Certificates already exist at $CERT_PATH"
fi

# Backwards compatibility with older filenames
cp "$CERT_PATH" "$CERT_DIR/dev.crt" >/dev/null 2>&1 || true
cp "$KEY_PATH" "$CERT_DIR/dev.key" >/dev/null 2>&1 || true
