COMPOSE := docker compose -f docker-compose.prod.yml

.DEFAULT_GOAL := help

.PHONY: help build up down migrate logs

help: ## List available targets with descriptions
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*##"}; {printf "  %-10s %s\n", $$1, $$2}'

build: ## Build the backend Docker image
	$(COMPOSE) build backend

up: ## Start all services in detached mode
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

migrate: ## Run Alembic migrations inside the backend container
	$(COMPOSE) exec backend alembic upgrade head

logs: ## Tail backend logs (Ctrl-C to stop)
	$(COMPOSE) logs -f backend
