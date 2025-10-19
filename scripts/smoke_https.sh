#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

command -v jq >/dev/null 2>&1 || { echo "[smoke_https] jq is required"; exit 1; }

# Start HTTPS stack
./scripts/dev_https.sh

# Basic checks
set -x
curl -sk https://localhost/health | jq .
curl -sk -X POST https://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"voter@example.com","password":"x"}' | jq .
curl -sk https://localhost/ballots | jq .
