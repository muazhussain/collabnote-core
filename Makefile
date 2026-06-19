.PHONY: dev run down clean \
        alembic-init alembic-revision migrate alembic-upgrade alembic-downgrade \
        alembic-history alembic-current alembic-heads \
        test test-fast test-file \
        lint lint-flake8 lint-black lint-mypy format shell logs help

dev:          ## Build images, run migrations, start everything (first-time setup)
	cp -n .env.example .env || true
	docker compose up --build

run:          ## Start all services without rebuild
	docker compose up

down:         ## Stop all services
	docker compose down

clean:        ## Stop services and wipe all volumes (fresh start)
	docker compose down -v

# ---- Alembic ----

alembic-init:      ## One-time: init alembic/ directory and alembic.ini
	docker compose run --rm api alembic init alembic

alembic-revision:  ## Generate migration  e.g.: make alembic-revision MSG="add users table"
	docker compose run --rm api alembic revision --autogenerate -m "$(MSG)"

migrate:           ## Apply all pending migrations (upgrade to head)
	docker compose run --rm migrator

alembic-upgrade:   ## Upgrade to specific revision  e.g.: make alembic-upgrade REV=abc123
	docker compose run --rm api alembic upgrade $(REV)

alembic-downgrade: ## Downgrade  e.g.: make alembic-downgrade REV=-1
	docker compose run --rm api alembic downgrade $(REV)

alembic-history:   ## Show full migration history
	docker compose run --rm api alembic history --verbose

alembic-current:   ## Show current applied revision
	docker compose run --rm api alembic current

alembic-heads:     ## Show current heads (detects diverging branches)
	docker compose run --rm api alembic heads

# ---- Testing ----

test:         ## Run full test suite with coverage report
	docker compose run --rm api pytest app/tests/ -v --cov=app --cov-report=term-missing

test-fast:    ## Run tests without coverage (faster feedback)
	docker compose run --rm api pytest app/tests/ -v

test-file:    ## Run single test file  e.g.: make test-file FILE=app/tests/test_api.py
	docker compose run --rm api pytest $(FILE) -v

# ---- Linting ----

lint:         ## Run all linters (flake8 + black + mypy)
	docker compose run --rm api sh -c "flake8 app/ && black --check app/ && mypy app/"

lint-flake8:  ## Run flake8 + flake8-docstrings only
	docker compose run --rm api flake8 app/

lint-black:   ## Run black check only
	docker compose run --rm api black --check app/

lint-mypy:    ## Run mypy type check only
	docker compose run --rm api mypy app/

format:       ## Auto-fix formatting with black (in-place)
	docker compose run --rm api black app/

# ---- Utils ----

shell:        ## Open bash shell in running api container
	docker compose exec api bash

logs:         ## Follow api logs
	docker compose logs -f api

help:         ## Show all make targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'