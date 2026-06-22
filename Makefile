.PHONY: help install run dev test lint format lint-fix pre-commit clean

APP_DIR := apps/team_datascience/mvip/unity_churn_dashboard

help:          ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:       ## Sync uv dependencies
	uv sync

run: install   ## Run dashboard locally (auto syncs first)
	uv run streamlit run $(APP_DIR)/app.py

dev: install   ## Run dashboard with auto-reload on save
	uv run streamlit run $(APP_DIR)/app.py --server.runOnSave true

test: install  ## Run tests with pytest
	uv run pytest tests/ -v

lint: install  ## Run ruff linter
	uv run ruff check .

format:        ## Run ruff formatter
	uv run ruff format .

lint-fix:      ## Run ruff linter with auto-fix
	uv run ruff check --fix .

pre-commit:    ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

clean:         ## Clean pycache and ruff cache
	rm -rf .ruff_cache __pycache__ .pytest_cache
