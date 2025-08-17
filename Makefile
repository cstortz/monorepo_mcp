.PHONY: install test lint format clean start-postgres start-fs start-all stop-all help

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean up temporary files"
	@echo "  start-postgres - Start PostgreSQL server"
	@echo "  start-fs    - Start filesystem server"
	@echo "  start-all   - Start all servers"
	@echo "  stop-all    - Stop all servers"

# Install dependencies
install:
	python3 -m venv venv
	. venv/bin/activate && pip install -e .

# Run tests
test:
	. venv/bin/activate && pytest tests/ -v

# Run linting
lint:
	. venv/bin/activate && flake8 src/ tests/
	. venv/bin/activate && mypy src/

# Format code
format:
	. venv/bin/activate && black src/ tests/

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "*.pid" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Start PostgreSQL server
start-postgres:
	. venv/bin/activate && python -m mcp_postgres

# Start filesystem server
start-fs:
	. venv/bin/activate && python -m mcp_filesystem

# Start all servers
start-all:
	./scripts/run-all-servers.sh

# Stop all servers
stop-all:
	./scripts/stop-all-servers.sh
