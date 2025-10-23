# Secure Systems Capstone – Voter System

Security-hardened electronic voting demo composed of a FastAPI backend, React/Vite frontend, and an HTTPS reverse proxy. The project showcases layered defenses—JWT auth, MFA, rate limiting, CAPTCHA/lockout guards, strict HTTP headers, TLS offload—while remaining easy to run locally for evaluation and coursework.

---

## At A Glance
- **Backend**: FastAPI + SQLAlchemy (SQLite) with login guards, MFA (TOTP + backup codes), JWT sessions, and rotating security logs.
- **Frontend**: React 18 + Vite + Tailwind with guarded routes, inactivity timeouts, MFA enrollment, and UX telemetry.
- **Proxy**: Dockerised Nginx enforcing HTTPS/HSTS for `/auth/*` and forwarding to the local API.
- **Tooling**: Python virtualenv, npm scripts, backup/restore utilities, and comprehensive pytest coverage of the security controls.

---

## Repository Layout
| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI application, SQLAlchemy models, security modules, tests, and backup scripts |
| `frontend/` | React/Vite client with admin & voter flows plus MFA tooling |
| `nginx/` | Dockerised TLS proxy config and certificate generator |
| `scripts/` | Helpers for starting HTTPS stack and smoke checks |
| `docker-compose.nginx.yml` | Compose file used by the HTTPS proxy helper |
| `encryption_service.py` | Stand-alone Fernet utility for encrypting/decrypting PII |
| `Makefile` | Common developer commands (`dev-https`, `test`, etc.) |

---

## Security & Compliance Features
- **REQ-05 TLS proxy**: `scripts/dev_https.sh` builds the Nginx container that terminates TLS, issues HSTS, and restricts traffic to `/auth/*`.
- **REQ-06 HTTP hardening**: Middleware in `backend/app/main.py` blocks PUT/DELETE on public endpoints and enforces `application/json` POST bodies.
- **REQ-10 PII encryption**: `encryption_service.py` demonstrates managed Fernet keys for protecting sensitive voter data.
- **REQ-13 client RBAC**: Frontend route guards (`frontend/src/App.tsx`) differentiate admin and voter dashboards, backed by JWT role claims.
- **REQ-16 UX telemetry**: Authenticated clients emit signed UX events via `frontend/src/lib/ux.ts`, logged server-side with `auth.log`.
- **REQ-17 Secure headers**: Global middleware sets CSP, X-Frame-Options, referrer, permissions policy, and Strict-Transport-Security.
- Additional safeguards: SlowAPI rate limiting, CAPTCHA/lockout guards (`app/security`), Argon2id password hashing with pepper, rotating auth logs, and inactivity-based auto-logout on both client and server.

---

## Prerequisites
- Python **3.11+** (project tested with 3.13) and `pip`
- Node.js **18+** (ships with npm)
- Docker Desktop (for running the HTTPS proxy)
- `openssl` (typically pre-installed; used when generating certificates)
- macOS/Linux/WSL shell with `bash`, `lsof`, and `jq`

---

## Backend (FastAPI)

### 1. Install dependencies
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Run the API
From the repository root:
```bash
PYTHONPATH=$PWD/backend backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The service listens on `http://127.0.0.1:8000`.

> **Note**: A starter SQLite database lives at `backend/app.db`. The primary admin credentials (`admin@evp-demo.com` / `secret123`) are hard-coded in `app/routers/auth.py` and protected by MFA—enroll before first login.

### 3. Environment configuration
Set variables before launching uvicorn as needed:
| Variable | Default | Description |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | Vite dev origins | CORS allowlist (comma-separated) |
| `ENABLE_LOGIN_GUARDS` | `1` | Toggle lockout + CAPTCHA guards |
| `LOGIN_FAIL_LIMIT` | `3` | Failed login attempts before lockout |
| `LOGIN_LOCKOUT_SECONDS` | `30` | Lockout duration |
| `LOGIN_CAPTCHA_FAIL_THRESHOLD` | `1` | Attempts before CAPTCHA required |
| `CAPTCHA_THRESHOLD` | `3` | Legacy CAPTCHA guard threshold |
| `CAPTCHA_VALID_TOKEN` | `1234` | Token expected when CAPTCHA required |
| `PASSWORD_PEPPER` | _(unset)_ | Optional Argon2 pepper (hex/base64 acceptable) |
| `JWT_SECRET` | `your-secret-key` | Symmetric signing key for JWTs |
| `JWT_ALGORITHM` | `HS256` | Algorithm used by `python-jose` |

### 4. Running tests
```bash
cd backend
PYTHONPATH=$PWD ../backend/.venv/bin/pytest -q
```
Tests cover rate limiting, login guards, MFA enrolment, CAPTCHA flows, RBAC, CORS, health check, and backup/restore scripts. Use `make test` from the repo root for convenience.

### 5. Database maintenance
- **Backups**: `python backend/scripts/backup_db.py`
- **Restores**: `python backend/scripts/restore_db.py --snapshot backups/snapshot-YYYYMMDD-HHMMSS.sqlite3`

Metadata (hash, integrity check, table counts) is written alongside each snapshot, and the restore script validates hashes before swapping files.

---

## Frontend (React + Vite)

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Configure API origin
`frontend/.env` defaults to the local HTTP API:
```
VITE_API_BASE=http://127.0.0.1:8000
```
Switch to `https://localhost` when using the TLS proxy.

### 3. Run the dev server
```bash
npm run dev
```
Open the printed URL (usually `http://localhost:5173`). Vite provides hot module reload for rapid iteration.

### 4. Build & lint
```bash
npm run build
npm run lint
```

---

## HTTPS Demo Stack (TLS Proxy)

1. Ensure the backend is **not** already bound to port 8000 (the script starts it if needed).
2. Run the helper from the repo root:
   ```bash
   ./scripts/dev_https.sh
   ```
   - Generates self-signed certs (stored in `nginx/certs/`)
   - Starts the FastAPI backend (recording `backend/.uvicorn.pid`)
   - Builds and runs the Nginx container listening on `443`
3. Access the API through the proxy at `https://localhost/auth/...` (use `-k` with curl for self-signed certs).
4. Stop the proxy and background uvicorn with:
   ```bash
   make tls-stop
   make stop
   ```

For basic end-to-end verification, run `./scripts/smoke_https.sh` (requires `jq`).

---

## Demo Workflows

### Admin (MFA protected)
1. Navigate to `http://localhost:5173/admin-login`.
2. First-time setup: visit `http://localhost:5173/mfa-enroll`, submit the default credentials, and scan the QR code (or copy the URI) into an authenticator app. Record the one-time backup codes.
3. Log in with:
   - Email: `admin@evp-demo.com`
   - Password: `secret123`
   - OTP or backup code (after failing without one you’ll see `mfa_required`)
   - Provide CAPTCHA token `1234` if prompted after failed attempts.
4. Admin dashboard displays tally data from `/ballots/tally`, auto-logs out after ~60s inactivity, and emits signed UX telemetry.

### Voter
1. Navigate to `http://localhost:5173/signup` to create a voter account (username constraints enforced in `Signup`).
2. Sign in at `/login` with your email/password. The flow adapts to CAPTCHA requirements and lockouts based on backend responses.
3. Cast votes via the user dashboard; per-ballot status is cached and enforced server-side (`/ballots/{id}/vote`).
4. Idle sessions trigger automatic logout on both client and server.

### API Exploration
Key endpoints (see `backend/app/routers/`):
- `/auth/login`, `/auth/signup`, `/auth/refresh`, `/auth/ux`
- `/auth/mfa/enroll`, `/auth/mfa/qrcode`, `/auth/mfa/verify-setup`
- `/ballots`, `/ballots/{id}`, `/ballots/{id}/vote`, `/ballots/tally`
- `/health` for readiness checks

All mutation endpoints require `application/json` requests; invalid verbs receive `405` from the HTTP hardening middleware.

---

## Logging & Observability
- **Authentication log**: `backend/auth.log` (managed by `logging.handlers.RotatingFileHandler`, 5 MB per file, 3 backups). Captures login attempts, lockouts, MFA failures, refreshes, and UX events.
- **UX telemetry**: `frontend/src/lib/ux.ts` sends signed events that are appended to the auth log for correlation.
- **SlowAPI rate limiting**: Exceeding limits returns HTTP 429 with `Retry-After` headers; login guards expose `X-Captcha-Required` to the client.

---

## Helpful Make Targets & Scripts
| Command | Description |
| --- | --- |
| `make dev` | Run backend with auto-reload (no TLS proxy) |
| `make dev-https` | Alias for `./scripts/dev_https.sh` |
| `make stop` | Kill uvicorn and clean PID file |
| `make tls-stop` | Stop the Nginx proxy container |
| `make test` | Execute backend pytest suite |

Additional helpers live in `scripts/` and `backend/scripts/`.

---

## Troubleshooting
- **Port 8000 already in use**: Check `backend/.uvicorn.pid` or run `lsof -i :8000` and stop the existing process before starting a new server.
- **Login locked out**: Wait for the lockout window (default 30 s) or reset guard state by toggling `ENABLE_LOGIN_GUARDS=0` temporarily.
- **TLS certificate warnings**: Self-signed certs are generated for local testing. Use `curl -k` or import `nginx/certs/localhost.crt` into your trust store.
- **CAPTCHA required**: Submit the `captcha_token` field with value `1234` (override via `CAPTCHA_VALID_TOKEN`).
- **JWT failures**: Ensure the frontend and backend share the same `JWT_SECRET`; restart uvicorn after changing secrets so the LRU cache updates.

---

## Contributing
1. Keep security features intact—tests are opinionated around rate limits, MFA, and guards.
2. Run `pytest -q` (backend) and `npm run lint` (frontend) before submitting changes.
3. Update this README when adding new requirements, scripts, or developer workflows.

Enjoy experimenting with secure-by-default patterns in a contained voter system demo!
