.PHONY: help install dev lint typecheck test test-unit test-integration coverage migrate seed run docker-up docker-down deploy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev: ## Install with dev dependencies
	uv sync --dev

lint: ## Run linter
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format: ## Auto-format code
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck: ## Run type checker
	uv run mypy src/

test: ## Run all tests
	uv run pytest -v

test-unit: ## Run unit tests only
	uv run pytest tests/unit -v

test-integration: ## Run integration tests
	uv run pytest tests/integration -v

coverage: ## Run tests with coverage
	uv run pytest --cov=fraud_engine --cov-report=term-missing --cov-report=html

migrate: ## Run database migrations
	uv run alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	uv run alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with mock data
	uv run python scripts/seed_data.py

run: ## Run development server
	uv run uvicorn fraud_engine.main:create_app --factory --reload --host 0.0.0.0 --port 8000

docker-up: ## Start all services with Docker Compose
	docker compose up --build -d

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Tail logs
	docker compose logs -f app

deploy: ## Build, push to ECR, and deploy to ECS
	./scripts/deploy.sh
