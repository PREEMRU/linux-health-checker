.PHONY: test lint install

test:
	uv run pytest

lint:
	uv run ruff check .

install:
	bash deploy/install.sh