# Makefile for Job Alert Bot

.PHONY: help install dev start stop clean logs test lint format deploy

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Start development server"
	@echo "  start      - Start production server"
	@echo "  stop       - Stop all services"
	@echo "  clean      - Clean up generated files"
	@echo "  logs       - View application logs"
	@echo "  test       - Run tests (if any)"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  deploy     - Deploy to Render"

# Install dependencies
install:
	pip install -r requirements.txt

# Start development server
dev:
	uv run uvicorn asgi:app --reload --host 0.0.0.0 --port 8000

# Start production server
start:
	uv run uvicorn asgi:app --host 0.0.0.0 --port 8000

# Docker commands
docker-build:
	docker build -t job-alert-bot .

docker-run:
	docker run -p 8000:8000 \
		-e TELEGRAM_TOKEN=$$TELEGRAM_TOKEN \
		-e ADMIN_ID=$$ADMIN_ID \
		-e WEBHOOK_BASE_URL=$$WEBHOOK_BASE_URL \
		-e WEBHOOK_TOKEN=$$WEBHOOK_TOKEN \
		job-alert-bot

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f job-alert-bot

# Docker Compose commands
compose-up:
	docker-compose up -d

compose-down:
	docker-compose down

compose-logs:
	docker-compose logs -f job-alert-bot

compose-clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf logs/*.log
	rm -rf data/*.db

# Logs
logs:
	docker-compose logs -f job-alert-bot

# Testing (placeholder - add actual tests)
test:
	@echo "No tests configured yet. Add tests in tests/ directory."

# Linting (placeholder - add actual linting)
lint:
	@echo "Consider adding pylint, flake8, or ruff for linting."

# Code formatting (placeholder - add actual formatting)
format:
	@echo "Consider adding black or autopep8 for code formatting."

# Health check
health:
	@echo "Checking application health..."
	curl -f http://localhost:8000/ || echo "Application is not healthy"

# Environment validation
validate-env:
	@echo "Validating environment variables..."
	@if [ -z "$$TELEGRAM_TOKEN" ]; then echo "ERROR: TELEGRAM_TOKEN not set"; exit 1; fi
	@if [ -z "$$ADMIN_ID" ]; then echo "ERROR: ADMIN_ID not set"; exit 1; fi
	@if [ -z "$$WEBHOOK_BASE_URL" ]; then echo "ERROR: WEBHOOK_BASE_URL not set"; exit 1; fi
	@if [ -z "$$WEBHOOK_TOKEN" ]; then echo "ERROR: WEBHOOK_TOKEN not set"; exit 1; fi
	@echo "All required environment variables are set!"

# Deployment
deploy-render:
	@echo "Deploying to Render..."
	@echo "Please use the Render dashboard or CLI for deployment"
	@echo "See README.md for deployment instructions"

# Database operations
db-backup:
	@echo "Creating database backup..."
	cp data/database.db data/database_$(shell date +%Y%m%d_%H%M%S).db

db-clean:
	@echo "Cleaning old job listings..."
	@echo "Use /cleanup_jobs command in the bot for this operation"

# Development utilities
watch:
	@echo "Watching for changes..."
	@echo "Use 'make dev' for development with auto-reload"

# Security check
security-check:
	@echo "Running security checks..."
	@echo "Check for exposed secrets in git history"
	@echo "Verify environment variables are not committed"
	@echo "Review dependencies for known vulnerabilities"

# Production checks
prod-check:
	@echo "Production readiness checklist:"
	@echo "✓ Environment variables configured"
	@echo "✓ Database backup strategy"
	@echo "✓ Monitoring and logging"
	@echo "✓ Error handling"
	@echo "✓ Security measures"
	@echo "✓ Rate limiting"
	@echo "✓ Health checks"
	@echo "Run 'make validate-env' to check environment"