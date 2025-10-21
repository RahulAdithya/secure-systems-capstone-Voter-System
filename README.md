# Test# build ping

## TLS Proxy for /auth/* (REQ-05)

```
# 0) Run backend locally (separate terminal)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 1) Generate self-signed certs
bash nginx/gen-cert.sh

# 2) Build and run the Nginx proxy
docker compose -f docker-compose.nginx.yml up --build -d

# 3) Verify HTTP → HTTPS redirect (301/308) for /auth/*
curl -i http://localhost/auth/login | sed -n '1,20p'
# Expect: HTTP/1.1 308 (or 301) and Location: https://localhost/auth/login

# 4) Verify HTTPS works and includes HSTS (self-signed: use -k)
curl -k -I https://localhost/auth/login | sed -n '1,20p'
# Expect: HTTP/1.1 200/405/401 (depends on backend route) and Strict-Transport-Security header

# 5) Bonus: proxy is only for /auth/*
curl -k -I https://localhost/ | sed -n '1,12p'
# Expect: 404 (by design)
```

## Frontend Theme Smoke Tests

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 (or 5174 if Vite selects another port) and verify:

- Theme matches your OS preference on first load.
- Using the theme toggle in the header switches light ↔ dark and persists after refresh.
- Pages (login, signup, dashboards) inherit the background/text colors and component styling.
- Keyboard tabbing shows visible focus rings on buttons, inputs, and links.
