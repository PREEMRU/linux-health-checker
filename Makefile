.PHONY: test lint install coverage

test:
	uv run pytest

lint:
	uv run ruff check .

install:
	bash deploy/install.sh

coverage:
	uv run pytest --cov=health --cov-report=term-missing --cov-fail-under=90