# {{ title }}

A notes API on Prisma 6 + SQLite + Express 5. The database is a single file, the
schema is a migration you can read, and rows survive a restart — `smoke.sh` proves
all three by killing the server and asking again.

```bash
npm install
npm run build     # prisma generate + tsc
npm test          # build, migrate, then node --test over a live socket
npm start         # node dist/src/server.js on $PORT (default 5467)
bash smoke.sh     # full contract: CRUD, 422s, 405s, 404 shape, restart persistence
```

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `200 {"status":"ok","notes":N}` |
| `GET` | `/notes` | `200` array, ordered by `id` |
| `POST` | `/notes` | `201` note, or `422 invalid_title` |
| `GET` | `/notes/:id` | `200` note, or `404 not_found` |
| `PATCH` | `/notes/:id` | `200` note with untouched fields preserved |
| `DELETE` | `/notes/:id` | `204` |
| any | unknown route | `404 {"error":"not_found","detail":"no route for GET /zzz"}` |
| any | wrong method | `405 method_not_allowed` |
| `POST` with broken JSON | | `422 invalid_json` |

## Layout

| Path | What it holds |
| --- | --- |
| `prisma/schema.prisma` | the `Note` model and a **literal** `file:./dev.db` URL |
| `prisma/migrations/0_init/` | the SQL Prisma replays on `migrate deploy` |
| `src/db.ts` | `NoteStore` — every query the app makes, plus the URL resolution |
| `src/app.ts` | routes and the error mapping; no Prisma import, so it is testable against a fake store |
| `src/server.ts` | the only place that listens |
| `tests/contract.test.ts` | the whole table above over a real socket on port 0 |

## Two traps this stack encodes

`prisma` resolves `file:./dev.db` **relative to `schema.prisma`**, so the CLI writes
`prisma/dev.db`; a runtime default of `./dev.db` is a *different file* that starts
empty and makes `migrate deploy` look like it did nothing. `src/db.ts` resolves the
root from `__dirname` and joins `prisma/dev.db`.

`app.all()` rather than `app.get()` is what turns an unsupported method into a `405`
instead of Express's own `404`.
