# Makefile for Flash Post API Testing

.PHONY: help test test-unit test-integration test-cov test-fast test-slow test-watch clean

# Default target
help:
	@echo "Available commands:"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-cov      - Run tests with coverage report"
	@echo "  test-fast     - Run fast tests only (exclude slow)"
	@echo "  test-slow     - Run slow tests only"
	@echo "  test-watch    - Run tests in watch mode"
	@echo "  test-debug    - Run tests with debug output"
	@echo "  clean         - Clean test artifacts"

# Run all tests
test:
	pytest

# Run unit tests only
test-unit:
	pytest -m unit

# Run integration tests only  
test-integration:
	pytest -m integration

# Run tests with coverage
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Run fast tests (exclude slow)
test-fast:
	pytest -m "not slow"

# Run slow tests only
test-slow:
	pytest -m slow

# Run tests in watch mode (requires pytest-watch)
test-watch:
	ptw --runner "pytest -v"

# Run tests with debug output
test-debug:
	pytest -v -s --tb=long

# Run tests for specific module
test-auth:
	pytest test/integration/test_auth.py -v

test-blogs:
	pytest test/integration/test_blogs.py -v

test-models:
	pytest test/unit/test_models.py -v

# Run tests with performance timing
test-perf:
	pytest --durations=10 -m performance

# Clean test artifacts
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install test dependencies
install-test-deps:
	uv add --dev pytest-asyncio pytest-cov pytest-mock pytest-timeout pytest-watch

# Setup test environment
setup-test:
	make install-test-deps
	@echo "Test environment setup complete!"
	@echo "Run 'make test' to run all tests"
