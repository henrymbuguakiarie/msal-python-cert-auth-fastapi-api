.PHONY: help install test lint format clean docker-build docker-up docker-down docs

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install all dependencies for API and client"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make pre-commit    - Install pre-commit hooks"
	@echo "  make security      - Run security checks"
	@echo "  make docs          - Generate API documentation"

# Installation
install:
	@echo "Installing API dependencies..."
	cd api && poetry install
	@echo "Installing client dependencies..."
	cd client && poetry install
	@echo "✓ Dependencies installed"

install-api:
	cd api && poetry install

install-client:
	cd client && poetry install

# Testing
test:
	@echo "Running API tests..."
	cd api && poetry run pytest -v --cov=src --cov-report=term-missing
	@echo "Running client tests..."
	cd client && poetry run pytest -v --cov=src --cov-report=term-missing

test-api:
	cd api && poetry run pytest -v --cov=src --cov-report=html --cov-report=term-missing

test-client:
	cd client && poetry run pytest -v --cov=src --cov-report=html --cov-report=term-missing

test-integration:
	cd api && poetry run pytest tests/integration -v

# Code Quality
lint:
	@echo "Running linters for API..."
	cd api && poetry run ruff check src tests
	@echo "Running linters for client..."
	cd client && poetry run ruff check src tests

format:
	@echo "Formatting API code..."
	cd api && poetry run black src tests
	cd api && poetry run isort src tests
	@echo "Formatting client code..."
	cd client && poetry run black src tests
	cd client && poetry run isort src tests
	@echo "✓ Code formatted"

format-check:
	cd api && poetry run black --check src tests
	cd api && poetry run isort --check-only src tests
	cd client && poetry run black --check src tests
	cd client && poetry run isort --check-only src tests

# Security
security:
	@echo "Running security checks..."
	cd api && poetry run bandit -r src -f screen || true
	cd api && poetry run safety check || true

# Pre-commit
pre-commit:
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

pre-commit-run:
	pre-commit run --all-files

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "✓ Services started"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/v1/docs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# Development
dev-api:
	cd api && poetry run python -m src.main

dev-client:
	cd client && poetry run python -m src.main

# Database
db-seed:
	cd api && poetry run python scripts/seed_data.py

db-seed-clear:
	cd api && poetry run python scripts/seed_data.py --clear

# Documentation
docs:
	cd api && poetry run python -c "from src.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > docs/openapi.json
	@echo "✓ API documentation generated"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf api/dist api/build client/dist client/build
	@echo "✓ Cleaned build artifacts"

# CI/CD simulation
ci:
	make format-check
	make lint
	make test
	make security
	@echo "✓ CI checks passed"
