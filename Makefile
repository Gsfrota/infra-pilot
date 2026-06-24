.PHONY: install dev lint test demo run audit mcp clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest

demo:
	infrapilot demo

run:
	infrapilot run

audit:
	infrapilot audit

mcp:
	infrapilot-mcp

clean:
	rm -rf .infrapilot .ruff_cache .pytest_cache **/__pycache__ *.egg-info
