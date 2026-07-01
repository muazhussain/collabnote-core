.PHONY: dev run down clean \
        alembic-init alembic-revision migrate alembic-upgrade alembic-downgrade \
        alembic-history alembic-current alembic-heads \
        test lint format shell logs help

POSTGRES_USER     ?= postgres
POSTGRES_PASSWORD ?= postgres
MONGO_USER        ?= mongo
MONGO_PASSWORD    ?= mongo

TEST_PG_URL    = postgresql+psycopg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/collabnote_test
TEST_REDIS_URL = redis://redis:6379/1
TEST_MONGO_URL = mongodb://$(MONGO_USER):$(MONGO_PASSWORD)@mongodb:27017

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

test:         ## Run tests (requires: make run)  e.g.: make test T=app/tests/test_auth.py
	docker compose exec postgres createdb -U $(POSTGRES_USER) collabnote_test 2>/dev/null || true
	docker compose run --rm --no-deps \
		-v $(CURDIR)/requirements.dev.txt:/app/requirements.dev.txt \
		-e DATABASE_URL=$(TEST_PG_URL) \
		-e REDIS_URL=$(TEST_REDIS_URL) \
		-e MONGODB_URL=$(TEST_MONGO_URL) \
		-e MONGODB_DB_NAME=collabnote_test \
		api sh -c "pip install -r requirements.dev.txt -q && pytest $(or $(T),app/tests/) -v --cov=app --cov-report=term-missing"; \
	EXIT=$$?; \
	docker compose exec postgres dropdb -U $(POSTGRES_USER) --if-exists collabnote_test; \
	exit $$EXIT

# ---- Linting ----

lint:         ## Run all linters (flake8 + black + mypy)
	flake8 app/ && black --check app/ && mypy app/

format:       ## Auto-fix formatting with black (in-place)
	black app/

# ---- Utils ----

shell:        ## Open bash shell in running api container
	docker compose exec api bash

logs:         ## Follow api logs
	docker compose logs -f api

help:         ## Show all make targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
