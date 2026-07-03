.PHONY: install dev test lint typecheck sec audit format clean

install:
	pip install -e .
	pip install -r requirements-dev.txt

dev:
	python main.py

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy .

sec:
	bandit -r . -c pyproject.toml

audit:
	pip-audit -r requirements.txt

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache dist/ dist.zip
	find . -type d -name "__pycache__" -exec rm -rf {} +
