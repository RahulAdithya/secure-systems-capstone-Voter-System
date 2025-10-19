
## HTTPS Dev One-Liner

- First time only: `bash nginx/gen-cert.sh`
- Daily: `make dev-https` (starts backend on :8000 if needed and launches the Nginx TLS proxy on :443)

Frontend config:
- With proxy: `VITE_API_BASE=https://localhost`
- Without proxy: `VITE_API_BASE=http://127.0.0.1:8000`

Stop only the proxy: `make tls-stop`  
Stop uvicorn: `make stop`
