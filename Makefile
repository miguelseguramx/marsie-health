.PHONY: help up down build logs shell migrate makemigrations superuser test lint format check seed \
        client-install client-build client-lint client-typecheck client-shell

help:
	@echo "Common targets:"
	@echo "  make up                Start the stack (web + db + client) in foreground"
	@echo "  make down              Stop the stack and remove containers"
	@echo "  make build             Rebuild images"
	@echo "  make logs              Tail logs"
	@echo "  make shell             Open a Django shell in the web container"
	@echo "  make migrate           Run Django migrations"
	@echo "  make makemigrations    Create new migrations"
	@echo "  make superuser         Create a Django superuser"
	@echo "  make test              Run pytest in the web container"
	@echo "  make lint              Run ruff check"
	@echo "  make format            Run ruff format"
	@echo "  make check             Backend + frontend lint + tests"
	@echo "  make seed              Load dummy domain data (idempotent)"
	@echo "  make client-install    Install JS deps inside the client container"
	@echo "  make client-build      Build the React client (vite build)"
	@echo "  make client-lint       Lint the React client"
	@echo "  make client-typecheck  Type-check the React client"
	@echo "  make client-shell      Open a shell inside the client container"

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

check: lint test client-typecheck client-lint

seed:
	docker compose exec web python manage.py seed_dummy_data

client-install:
	docker compose run --rm client npm install

client-build:
	docker compose run --rm client npm run build

client-lint:
	docker compose run --rm client npm run lint

client-typecheck:
	docker compose run --rm client npm run typecheck

client-shell:
	docker compose exec client sh
