#!/usr/bin/env bash
set -euo pipefail

# Run from repo root regardless of where invoked
cd "$(dirname "$0")/.."

# 0) Check deps early
command -v docker >/dev/null 2>&1 || { echo "[dev_https] docker is required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "[dev_https] docker compose plugin is required"; exit 1; }
command -v lsof >/dev/null 2>&1 || { echo "[dev_https] lsof is required"; exit 1; }

# 1) Ensure self-signed certs exist (one-time)
if [ ! -f "nginx/certs/localhost.crt" ] || [ ! -f "nginx/certs/localhost.key" ]; then
  echo "[dev_https] generating self-signed certs..."
  bash nginx/gen-cert.sh
fi

# 2) Start backend if not already listening on :8000 (dev mode)
if ! lsof -i :8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[dev_https] starting FastAPI on :8000"
  (
    cd backend
    # Prefer project virtualenv if present
    PY_CMD="python3"
    if [ -x ".venv/bin/python" ]; then
      PY_CMD="$(pwd)/.venv/bin/python"
    elif command -v python >/dev/null 2>&1; then
      PY_CMD="python"
    fi
    PYTHONPATH=$PWD "$PY_CMD" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    echo $! > .uvicorn.pid
  )
  # small wait so nginx healthcheck won’t race
  sleep 1
else
  echo "[dev_https] backend already listening on :8000"
fi

# 3) Start/restart Nginx TLS proxy (idempotent)
echo "[dev_https] starting TLS proxy on :443 via docker compose"
docker compose -f docker-compose.nginx.yml up -d

# 4) Print helpful info
echo
echo "[dev_https] ✅ HTTPS ready at: https://localhost"
echo "[dev_https]    Backend (no proxy): http://127.0.0.1:8000"
echo "[dev_https]    Frontend .env for proxy:  VITE_API_BASE=https://localhost"
echo "[dev_https]    Frontend .env without:     VITE_API_BASE=http://127.0.0.1:8000"
