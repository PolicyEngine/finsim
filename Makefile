# FinSim Makefile using uv

.PHONY: install format test build clean docs

# Install dependencies and package in development mode
install:
	uv pip install -e ".[dev]"

# Install with all optional dependencies
install-all:
	uv pip install -e ".[dev,docs,app,enhanced]"

# Format code
format:
	uv run black finsim tests --line-length 88
	uv run ruff check --fix finsim tests

# Run tests
test:
	uv run pytest tests -v

# Run tests with coverage
test-cov:
	uv run pytest tests --cov=finsim --cov-report=term-missing --cov-report=html

# Type checking
mypy:
	uv run mypy finsim

# Build documentation
docs:
	uv run jupyter-book build docs/

# Build package
build:
	uv build

# Clean build artifacts
clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the Streamlit app
app:
	uv run streamlit run app.py

# Create virtual environment
venv:
	uv venv

# Sync dependencies from pyproject.toml
sync:
	uv sync

# Update dependencies
update:
	uv pip compile pyproject.toml -o requirements.txt
	uv pip sync requirements.txt

# Development workflow
dev: format test

# Full CI workflow
ci: install format test mypy

# Publish to PyPI
publish: clean build
	uv publish