
# Use a dedicated compose env file to avoid `.env` interpolation issues (bcrypt `$...`).
COMPOSE_ENV ?= .env.compose
COMPOSE ?= docker-compose --env-file $(COMPOSE_ENV)
COMPOSE_PROD ?= docker-compose --env-file $(COMPOSE_ENV) -f docker-compose.prod.yml

# Development
dev:
	$(COMPOSE) up --build

# Development (detached)
dev-d:
	$(COMPOSE) up --build -d

# Production
prod:
	$(COMPOSE_PROD) up --build -d

# Stop all
stop:
	$(COMPOSE) down
	$(COMPOSE_PROD) down

# Run migrations
migrate:
	$(COMPOSE) exec -T api alembic upgrade head

migrate-prod:
	$(COMPOSE_PROD) exec -T api alembic upgrade head

# Reset dev DB volume (fixes role/password mismatch when volume persists)
reset-db:
	$(COMPOSE) down -v

ps:
	$(COMPOSE) ps

ps-prod:
	$(COMPOSE_PROD) ps

test:
	$(COMPOSE) exec -T api python -m pytest -q

logs:
	$(COMPOSE) logs -f --tail=200

logs-prod:
	$(COMPOSE_PROD) logs -f --tail=200

logs-api:
	$(COMPOSE) logs -f --tail=200 api

logs-db:
	$(COMPOSE) logs -f --tail=200 db

logs-frontend:
	$(COMPOSE) logs -f --tail=200 frontend

shell-api:
	$(COMPOSE) exec api sh

shell-db:
	$(COMPOSE) exec db sh

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

BACKUP_DIR ?= backups
DB_BACKUP_FILE ?= $(BACKUP_DIR)/db_$(shell date +%Y%m%d_%H%M%S).sql

backup-db:
	mkdir -p $(BACKUP_DIR)
	$(COMPOSE) exec -T db sh -lc 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' > $(DB_BACKUP_FILE)
	@echo "Saved: $(DB_BACKUP_FILE)"

restore-db:
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backups/your.sql"; exit 2; fi
	cat $(FILE) | $(COMPOSE) exec -T db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'
