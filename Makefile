UV_VERSION ?= 0.10.9
SHELL := /bin/bash

# ==============================================================================
# UV rules
# ==============================================================================
install-uv:
	curl -LsSf https://astral.sh/uv/$(UV_VERSION)/install.sh | sh
	
install-python: install-uv
	uv python install $$(cat .python-version)

uv.%:
	uv run $(MAKE) $*

# ==============================================================================
# Developer rules
# ==============================================================================

install:
	uv sync

test:
	pytest -vv --cov masstransit

test-all:
	uv run -p 3.10 --all-groups -m pytest
	uv run -p 3.11 --all-groups -m pytest
	uv run -p 3.12 --all-groups -m pytest
	uv run -p 3.13 --all-groups -m pytest
	uv run -p 3.14 --all-groups -m pytest

format:
	ruff format masstransit/
	ruff check masstransit/ --fix-only

check-format:
	ruff format --check masstransit/

lint:
	ruff check masstransit/
	ty check masstransit

# ==============================================================================
# CI/CD rules
# ==============================================================================

step-install: install-uv install-python install

step-run-tests: check-format lint test-all

