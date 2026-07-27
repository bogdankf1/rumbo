.PHONY: up dev-db dev-backend dev-frontend test eval

up:
	docker compose up --build

dev-db:
	docker compose up -d --wait db

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test: dev-db
	cd backend && uv run pytest -q

eval:
	@curl -sf http://localhost:8000/health > /dev/null || (echo "Backend not reachable at :8000. Run 'make dev-db' and 'make dev-backend' (or 'make up') first." && exit 1)
	cd backend && uv run python -m evals.run
