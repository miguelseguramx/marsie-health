# marsie-health

Django backend service for Marsie Health.

## Stack

- Python 3.12 + Django 5 + Django REST Framework
- PostgreSQL 16
- Docker Compose for local development
- Ruff (lint + format), pytest-django, pre-commit

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

The web service will be available at http://localhost:8000.
Health check: http://localhost:8000/healthz/ → `{"status":"ok"}`.

## Common tasks

```bash
make migrate          # apply migrations
make makemigrations   # create new migrations
make test             # run pytest in the web container
make lint             # ruff check
make format           # ruff format
make superuser        # create a Django admin user
make shell            # open a Django shell
```

## Project layout

```
apps/
├── core/         # health-check, base views
└── hemogramas/   # CBC / hemograma domain (placeholder)
marsie_health/    # Django config (settings, urls, wsgi/asgi)
tests/            # pytest suite
```

## Environment variables

See `.env.example` for the full list. Notable ones:

- `DJANGO_SECRET_KEY` — required, no default.
- `DJANGO_DEBUG` — defaults to `False`. Set to `1` for local dev.
- `DJANGO_ALLOWED_HOSTS` — comma-separated.
- `DATABASE_URL` — Postgres connection string consumed by `django-environ`.

## Deployment

The Dockerfile defaults to `runserver` for local development. For production,
override the command to use gunicorn:

```bash
gunicorn marsie_health.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Branching

`main` is protected:

- No direct pushes — work happens on feature branches.
- PRs to `main` require 1 approval and a passing CI run.
- Linear history is enforced (squash or rebase merges).

## License

Apache License 2.0. See [LICENSE](./LICENSE).
