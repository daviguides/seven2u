.PHONY: up down logs test lint dev-backend dev-frontend build-frontend

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f app

test:
	cd backend && .venv/bin/python -m pytest -q

lint:
	cd backend && .venv/bin/ruff format --check app tests && .venv/bin/ruff check app tests

dev-backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 7777

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build && rm -rf ../backend/static && cp -r dist ../backend/static
