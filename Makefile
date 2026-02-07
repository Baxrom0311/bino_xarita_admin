# ============================================================
# Bino Xarita Admin - Makefile
# ============================================================
# Ishlatish: make <command>
# ============================================================

.PHONY: dev dev-d prod stop restart migrate test logs shell backup-db restore-db clean help

# Default .env file
ENV_FILE ?= .env

# Docker Compose with env file
COMPOSE = docker compose --env-file $(ENV_FILE)

# ========================
# DEVELOPMENT
# ========================

# Development mode (attached - loglarni ko'rish)
dev:
	$(COMPOSE) up --build

# Development mode (detached - background)
dev-d:
	$(COMPOSE) up --build -d

# ========================
# PRODUCTION
# ========================

# Production mode
prod:
	API_COMMAND="gunicorn -c gunicorn_conf.py app.main:app" \
	API_USER="app" \
	FRONTEND_TARGET="prod" \
	FRONTEND_COMMAND='nginx -g "daemon off;"' \
	FRONTEND_INTERNAL_PORT="80" \
	$(COMPOSE) up --build -d

# ========================
# CONTROL
# ========================

# Stop all containers
stop:
	$(COMPOSE) down

# Restart all
restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

# Status
ps:
	$(COMPOSE) ps

# ========================
# DATABASE
# ========================

# Run migrations
migrate:
	$(COMPOSE) exec -T api alembic upgrade head

# Reset database (WARNING: deletes all data!)
reset-db:
	$(COMPOSE) down -v
	@echo "Database volume deleted. Run 'make dev-d && make migrate' to recreate."

# Backup database
BACKUP_DIR ?= backups
backup-db:
	mkdir -p $(BACKUP_DIR)
	$(COMPOSE) exec -T db sh -lc 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' > $(BACKUP_DIR)/db_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to $(BACKUP_DIR)/"

# Restore database
restore-db:
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backups/your.sql"; exit 2; fi
	cat $(FILE) | $(COMPOSE) exec -T db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

# ========================
# TESTING
# ========================

# Run tests
test:
	$(COMPOSE) exec -T api python -m pytest -q

# Run tests with coverage
test-cov:
	$(COMPOSE) exec -T api python -m pytest --cov=app --cov-report=html

# ========================
# LOGS
# ========================

# All logs
logs:
	$(COMPOSE) logs -f --tail=200

# API logs only
logs-api:
	$(COMPOSE) logs -f --tail=200 api

# Database logs only
logs-db:
	$(COMPOSE) logs -f --tail=200 db

# Frontend logs only
logs-frontend:
	$(COMPOSE) logs -f --tail=200 frontend

# ========================
# SHELL ACCESS
# ========================

# API shell
shell-api:
	$(COMPOSE) exec api sh

# Database shell
shell-db:
	$(COMPOSE) exec db sh

# ========================
# CLEANUP
# ========================

# Clean up everything (containers, volumes, images)
clean:
	$(COMPOSE) down -v --rmi local
	@echo "Cleaned up containers, volumes, and local images."

# ========================
# HELP
# ========================

help:
	@echo "Bino Xarita Admin - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start in dev mode (attached)"
	@echo "  make dev-d      - Start in dev mode (detached)"
	@echo "  make prod       - Start in production mode"
	@echo ""
	@echo "Control:"
	@echo "  make stop       - Stop all containers"
	@echo "  make restart    - Restart all containers"
	@echo "  make ps         - Show container status"
	@echo ""
	@echo "Database:"
	@echo "  make migrate    - Run Alembic migrations"
	@echo "  make reset-db   - Delete database volume"
	@echo "  make backup-db  - Backup database to backups/"
	@echo "  make restore-db FILE=path/to/file.sql - Restore database"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage"
	@echo ""
	@echo "Logs:"
	@echo "  make logs       - All logs"
	@echo "  make logs-api   - API logs"
	@echo "  make logs-db    - Database logs"
	@echo ""
	@echo "Shell:"
	@echo "  make shell-api  - API container shell"
	@echo "  make shell-db   - Database container shell"
	@echo ""
	@echo "Options:"
	@echo "  ENV_FILE=.env.custom make dev  - Use custom env file"
