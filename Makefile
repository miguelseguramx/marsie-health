.PHONY: help up down build logs shell migrate makemigrations superuser test lint format check

help:
	@echo "Common targets:"
	@echo "  make up               Start the stack (web + db) in foreground"
	@echo "  make down             Stop the stack and remove containers"
	@echo "  make build            Rebuild images"
	@echo "  make logs             Tail logs"
	@echo "  make shell            Open a Django shell in the web container"
	@echo "  make migrate          Run Django migrations"
	@echo "  make makemigrations   Create new migrations"
	@echo "  make superuser        Create a Django superuser"
	@echo "  make test             Run pytest in the web container"
	@echo "  make lint             Run ruff check"
	@echo "  make format           Run ruff format"
	@echo "  make check            Lint + tests"

up:
	docker compose up

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

superuser:
	docker compose exec web python manage.py createsuperuser

test:
	docker compose exec web pytest

lint:
	docker compose exec web ruff check .

format:
	docker compose exec web ruff format .

check: lint test
