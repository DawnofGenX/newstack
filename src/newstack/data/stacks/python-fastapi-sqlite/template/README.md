# {{ title }}

{{ description }}

A JSON API over one SQLite file: `db.py` opens a connection per request with
WAL and a busy timeout, `migrations.py`-style SQL files are applied in order and
recorded, `routes.py` is the CRUD surface, and `main.py` migrates on startup.

## Layout

```
pyproject.toml               packaging, dependencies, ruff and pytest config
migrations/001_notes.sql     the schema, applied once and recorded
src/{{ package_name }}/db.py       connections, pragmas, the migration runner
src/{{ package_name }}/routes.py   notes CRUD, validation, 404 details
src/{{ package_name }}/main.py     app factory, migrations on startup
tests/test_api.py            one database per test, migrations twice
notes.db                     created on first run (gitignored, with -wal/-shm)
```

## Run

```sh
uv sync
uv run uvicorn {{ package_name }}.main:app --reload
curl -s -X POST localhost:8000/notes -H 'content-type: application/json' \
  -d '{"title":"shopping","body":"milk"}'
curl -s localhost:8000/notes
```

`DB_PATH` points the service at another database file.

## Traps this starter already paid for

- `sqlite3.executescript` COMMITS before it runs, so wrapping it in `with
  connection:` does not make the migration atomic. The transaction is opened
  inside the script (`BEGIN; … COMMIT;`) together with the row that records the
  migration.
- `check_same_thread=False` is mandatory: FastAPI runs sync handlers in a
  threadpool, and a connection created on the event-loop thread is otherwise
  rejected with `SQLite objects created in a thread can only be used in that
  same thread`.
- `PRAGMA journal_mode=WAL`, `foreign_keys` and `busy_timeout` are per
  CONNECTION, not per database file — every new connection sets them again.
- WAL leaves `notes.db-wal` and `notes.db-shm` next to the database; both belong
  in `.gitignore` or the first run dirties the tree.
- `TestClient(app)` as a plain value never runs the lifespan, so migrations
  would not happen. Use it as a context manager (`with TestClient(app) as c:`).
- SQLite has no `updated_at ON UPDATE`; the patch route writes
  `strftime('%Y-%m-%dT%H:%M:%fZ','now')` explicitly.
