
DEV  = docker compose -f docker-compose.yml -f docker-compose.monitoring.yml
PROD = docker compose -f docker-compose.product.yml -f docker-compose.monitoring.yml

.PHONY: help setup up down logs ps test lint prod-up prod-down

help:            ## показать список команд
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -/'

setup:
	@test -f .env || (cp .env.example .env && echo "Создан .env: впиши пароли db_password и grafana_admin_password")
	@bash scripts/gen-certs.sh

up:              
	$(DEV) up -d --build

down:            
	$(DEV) down

logs:
	$(DEV) logs -f --tail=50

ps:              
	$(DEV) ps

test:            
	pytest

lint:            
	ruff check . && ruff format --check .

prod-up:         
	$(PROD) pull && $(PROD) up -d

prod-down:
	$(PROD) down
