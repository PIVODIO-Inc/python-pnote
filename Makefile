# Makefile for PNote project code quality and development tasks

.PHONY: help format lint type-check test test-cov clean install-dev

# Default target
help:
	@echo "Available targets:"
	@echo "  format      - Format code with ruff"
	@echo "  lint        - Check code formatting and linting with ruff"
	@echo "  type-check  - Run type checking with mypy"
	@echo "  quality     - Run all code quality checks (lint + type-check)"
	@echo "  test        - Run tests with pytest"
	@echo "  test-cov    - Run tests with coverage report"
	@echo "  clean       - Clean up generated files"
	@echo "  install-dev - Install development dependencies"

# Format code with ruff
format:
	@echo "Formatting code with ruff..."
	uv run ruff format . --config pyproject.toml

# Check code formatting and linting with ruff
lint:
	@echo "Checking code formatting and linting with ruff..."
	uv run ruff check . --config pyproject.toml

# Run type checking with mypy
type-check:
	@echo "Running type checking with mypy..."
	uv run mypy pnote/

# Run all code quality checks
quality: lint type-check

# Run tests with pytest
test:
	@echo "Running tests..."
	uv run pytest tests/

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	uv run pytest --cov=pnote --cov-report=term-missing --cov-report=html tests/

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	uv sync --group dev

# Fix linting issues automatically
fix:
	@echo "Auto-fixing linting issues..."
	uv run ruff check --fix . --config pyproject.toml

# Full development workflow
dev: format fix test-cov type-check
	@echo "Development workflow completed!"
