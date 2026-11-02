# {{ title }}

{{ description }}

A [Django](https://www.djangoproject.com/) 6 application with a JSON API app (`core`), SQLite
storage, pytest-django tests and ruff linting.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

The server listens on http://127.0.0.1:8000/.

## Endpoints

| Method | Path      | Response                                             |
| ------ | --------- | ---------------------------------------------------- |
| GET    | `/health` | `{"status": "ok"}`                                   |
| GET    | `/items`  | JSON array of `{"id", "name", "created"}` records    |
| GET    | `/admin/` | Django admin (create a superuser with `createsuperuser`) |

## Configuration

Settings live in `config/settings.py` and read two environment variables:

| Variable            | Default                                | Notes                          |
| ------------------- | -------------------------------------- | ------------------------------ |
| `DJANGO_SECRET_KEY` | dev-only insecure key                  | **required** in production     |
| `DJANGO_DEBUG`      | `1`                                    | set to `0` for production      |

`ALLOWED_HOSTS` is `["*"]` for local development; tighten it before deploying.

## Development

```bash
uv sync
uv run python manage.py makemigrations   # after changing core/models.py
uv run pytest
uv run ruff check .
```

## Project layout

```
config/            settings, root URLconf, WSGI/ASGI entry points
core/              app: Item model, JSON views, migrations
tests/             pytest-django tests
manage.py          Django management entry point
```

## CI

`.github/workflows/ci.yml` runs lint, a migration-drift check and the test suite on Python 3.12
and 3.13 for every push to `main` and every pull request.

## License

MIT — see [LICENSE](LICENSE).
