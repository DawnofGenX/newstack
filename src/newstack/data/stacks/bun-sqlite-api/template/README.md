# {{ project_name }}

A notes API on Bun with **zero dependencies**: `Bun.serve()` for HTTP, `bun:sqlite`
for storage, `bun:test` for the suite. The interesting part is not the CRUD — it is
that every claim here is checked against a real socket and a real file.

## Run it

```bash
bun test                       # bun:test suite, server on an ephemeral port
bun run src/main.js --selftest # offline assertions, no socket bound
bun run src/main.js            # serve on 127.0.0.1:5471 (PORT / HOST / DB_PATH)
bash smoke.sh                  # the full contract against a live server
```

`PORT` must be numeric or the process exits 2. `DB_PATH` defaults to `./notes.db`.

## Routes

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| GET | `/health` | `200 {"status":"ok","notes":N}` | |
| POST | `/notes` | `201` note, keys `id,title,body,created_at`; `body` optional → `""` | `422` blank title / bad JSON |
| GET | `/notes` | `200 {"notes":[…oldest first…]}` | |
| GET | `/notes/{id}` | `200` note | `404` |
| PATCH | `/notes/{id}` | `200` updated note, untouched fields and `created_at` preserved | `404`, `422` |
| DELETE | `/notes/{id}` | `204` empty | `404` on the second delete |
| wrong method | any known path | | `405 {"error":"method_not_allowed"}` |

## Traps this starter already paid for

1. **`bun:sqlite` has no `db.pragma()` helper.** `db.exec("PRAGMA …")` silently
   *discards* the result, so WAL mode looks applied and is not. Read pragmas through
   `db.query("PRAGMA journal_mode = WAL").get()` and assert the value.
2. **PRAGMAs are per connection.** `journal_mode`, `busy_timeout` and `foreign_keys`
   are set in `openDb()` for *every* connection, not once at boot — the second
   connection the tests open is exactly where a "set it once" bug shows up.
3. **Migrations run inside `db.transaction()`.** `bun:sqlite`'s transaction helper is
   synchronous: an `await` inside it commits early and leaves half a schema behind.
   Read each `.sql` file *before* the transaction, then apply and record in one step.
4. **`Bun.scanDir` does not exist** in 1.4.x (the docs suggest it does). Migration
   discovery goes through `node:fs` — `readdirSync` plus `sort()`.
5. **JSON key order is insertion order.** The contract fixes `id,title,body,created_at`,
   so rows are reshaped by `noteShape()` rather than serialised as they come out of
   sqlite. A `SELECT *` change would silently reorder the wire format.
6. **`Bun.serve({ routes })` answers its own 404/405 in some paths.** The `fallback`
   handler is what makes the error bodies yours (and JSON) instead of Bun's default.
7. **A server that is `kill -TERM`ed may still hold the port.** `smoke.sh` waits for the
   child, and escalates to `SIGKILL` in its `EXIT` trap, because a leaked listener makes
   the *next* run fail with a confusing "port already answering".
8. **Instance state is a file, not a variable.** The restart test in `smoke.sh` stops the
   process and boots another on the same `DB_PATH`, then asserts the row is still there
   *and* that no phantom row appeared.
