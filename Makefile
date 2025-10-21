.PHONY: dev dev-https tls-stop stop seed db-upgrade db-reset test

dev:
	@cd backend && PYTHONPATH=$$(pwd) uvicorn app.main:app --reload

dev-https:
	@./scripts/dev_https.sh

tls-stop:
	@docker compose -f docker-compose.nginx.yml down

stop:
	@-pkill -f "uvicorn app.main:app" || true
	@-rm -f backend/.uvicorn.pid || true

db-upgrade:
	@cd backend && PERSISTENCE=sqlite DATABASE_URL=sqlite:///./dev.db python -m alembic upgrade head

db-reset:
	@cd backend && rm -f dev.db && PERSISTENCE=sqlite DATABASE_URL=sqlite:///./dev.db python -m alembic upgrade head

seed:
	@cd backend && PERSISTENCE=sqlite DATABASE_URL=sqlite:///./dev.db python scripts/seed.py

test:
	@cd backend && PYTHONPATH=$$(pwd) pytest -q
