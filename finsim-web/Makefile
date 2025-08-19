# FinSim Web Application Makefile

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(BLUE)FinSim Web Application Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install        - Install all dependencies (backend + frontend)"
	@echo "  make dev           - Run both frontend and backend in development mode"
	@echo "  make backend       - Run backend server only"
	@echo "  make frontend      - Run frontend server only"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test          - Run all tests (backend + frontend)"
	@echo "  make test-backend  - Run backend tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make test-watch    - Run frontend tests in watch mode"
	@echo ""
	@echo "$(GREEN)Building:$(NC)"
	@echo "  make build         - Build production version"
	@echo "  make docker        - Build and run with Docker"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make clean         - Clean build artifacts and caches"
	@echo "  make format        - Format code (Python + JS/TS)"
	@echo "  make lint          - Run linters"

# Installation
.PHONY: install
install: install-backend install-frontend
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

.PHONY: install-backend
install-backend:
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && pip install -r requirements.txt

.PHONY: install-frontend
install-frontend:
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install

# Development servers
.PHONY: dev
dev:
	@echo "$(BLUE)Starting development servers...$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:5001$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop both servers$(NC)"
	@npx concurrently -k \
		-p "[{name}]" \
		-n "Backend,Frontend" \
		-c "cyan,magenta" \
		"cd backend && uv run python app.py" \
		"cd frontend && npm run dev"

.PHONY: backend
backend:
	@echo "$(BLUE)Starting backend server...$(NC)"
	@echo "$(YELLOW)API running at: http://localhost:5001$(NC)"
	cd backend && uv run python app.py

.PHONY: frontend
frontend:
	@echo "$(BLUE)Starting frontend server...$(NC)"
	@echo "$(YELLOW)App running at: http://localhost:3000$(NC)"
	cd frontend && npm run dev

# Testing
.PHONY: test
test: test-backend test-frontend
	@echo "$(GREEN)✓ All tests passed$(NC)"

.PHONY: test-backend
test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd backend && uv run python -m pytest tests/ -v

.PHONY: test-backend-coverage
test-backend-coverage:
	@echo "$(BLUE)Running backend tests with coverage...$(NC)"
	cd backend && uv run python -m pytest tests/ -v --cov=. --cov-report=term-missing

.PHONY: test-frontend
test-frontend:
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd frontend && npm test -- --run

.PHONY: test-watch
test-watch:
	@echo "$(BLUE)Running frontend tests in watch mode...$(NC)"
	cd frontend && npm test

.PHONY: test-frontend-coverage
test-frontend-coverage:
	@echo "$(BLUE)Running frontend tests with coverage...$(NC)"
	cd frontend && npm run test:coverage

# Building
.PHONY: build
build: build-frontend
	@echo "$(GREEN)✓ Build complete$(NC)"

.PHONY: build-frontend
build-frontend:
	@echo "$(BLUE)Building frontend for production...$(NC)"
	cd frontend && npm run build

# Docker
.PHONY: docker
docker:
	@echo "$(BLUE)Building and running with Docker...$(NC)"
	docker-compose up --build

.PHONY: docker-build
docker-build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

.PHONY: docker-up
docker-up:
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up

.PHONY: docker-down
docker-down:
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down

.PHONY: docker-logs
docker-logs:
	docker-compose logs -f

# Code quality
.PHONY: format
format: format-backend format-frontend
	@echo "$(GREEN)✓ Code formatted$(NC)"

.PHONY: format-backend
format-backend:
	@echo "$(BLUE)Formatting Python code...$(NC)"
	cd backend && black . --line-length 100
	cd backend && isort .

.PHONY: format-frontend
format-frontend:
	@echo "$(BLUE)Formatting TypeScript/JavaScript code...$(NC)"
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,js,jsx,css}"

.PHONY: lint
lint: lint-backend lint-frontend
	@echo "$(GREEN)✓ Linting complete$(NC)"

.PHONY: lint-backend
lint-backend:
	@echo "$(BLUE)Linting Python code...$(NC)"
	cd backend && pylint *.py || true

.PHONY: lint-frontend
lint-frontend:
	@echo "$(BLUE)Linting TypeScript/JavaScript code...$(NC)"
	cd frontend && npm run lint

# Cleaning
.PHONY: clean
clean:
	@echo "$(BLUE)Cleaning build artifacts and caches...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"

# Quick start for new developers
.PHONY: setup
setup: install
	@echo ""
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)To start developing, run:$(NC)"
	@echo "  make dev"
	@echo ""
	@echo "$(YELLOW)To run tests:$(NC)"
	@echo "  make test"

# Install development dependencies globally (one-time setup)
.PHONY: install-dev-tools
install-dev-tools:
	@echo "$(BLUE)Installing development tools...$(NC)"
	npm install -g concurrently
	pip install black isort pylint pytest pytest-cov

# Check if all dependencies are installed
.PHONY: check-deps
check-deps:
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)✗ Python 3 is not installed$(NC)"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "$(RED)✗ Node.js is not installed$(NC)"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "$(RED)✗ npm is not installed$(NC)"; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)✗ uv is not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All required tools are installed$(NC)"

# Run a specific backend API endpoint test
.PHONY: test-api
test-api:
	@echo "$(BLUE)Testing API endpoints...$(NC)"
	@curl -s http://localhost:5001/api/health | python3 -m json.tool || echo "$(RED)Backend not running. Start with 'make backend'$(NC)"

# Open the application in browser
.PHONY: open
open:
	@echo "$(BLUE)Opening application in browser...$(NC)"
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 in your browser"

# Watch for file changes and restart backend
.PHONY: watch-backend
watch-backend:
	@echo "$(BLUE)Starting backend with auto-reload...$(NC)"
	cd backend && uv run python app.py

# Production run with gunicorn
.PHONY: prod
prod:
	@echo "$(BLUE)Starting production servers...$(NC)"
	@npx concurrently -k \
		-p "[{name}]" \
		-n "Backend,Frontend" \
		-c "cyan,magenta" \
		"cd backend && gunicorn app:app --bind 0.0.0.0:5001 --workers 4" \
		"cd frontend && npm run preview"

.DEFAULT_GOAL := help