# {{ npm_name }}

A notes service on axum + sqlx/SQLite: migrations live in `migrations/` and are
embedded in the binary, so the schema ships with the code.

| Method | Path | Answer |
| --- | --- | --- |
| GET | `/health` | `{"status":"ok","notes":N}` |
| GET | `/notes` | `{"notes":[{"id","title","body","created_at"}]}` |
| POST | `/notes` | 201 with the created note; `{"title","body"}` |
| GET | `/notes/{id}` | the note, or 404 `{"error":"not_found","detail":"no note with id N"}` |
| PATCH | `/notes/{id}` | the patched note; untouched fields survive |
| DELETE | `/notes/{id}` | 204 |
| any other | — | 404 `{"error":"not_found","detail":"no route for METHOD /path"}` |
| wrong method | `/health`, `/notes`, `/notes/{id}` | 405 `{"error":"method_not_allowed"}` |

Blank or missing titles answer 422 `invalid_request` with a `detail`; a body
that is not JSON answers 422 `invalid_json` with no `detail`.

## Run it

```sh
cargo build --release
DB_PATH=notes.db PORT=5470 ./bin/{{ npm_name }}
bash smoke.sh          # the same contract the repo gate runs
```

`--selftest` runs the offline assertions (no socket, no database file).
`cargo test` runs the four integration tests against a real SQLite temp file.

## Traps this starter already paid for

1. `sqlx::migrate!` is gated behind the `macros` feature. With only
   `["runtime-tokio","sqlite","migrate"]` the build fails
   `error[E0433]: cannot find migrate in sqlx`.
2. A `str::len()` is already a byte count; clippy's `needless_as_bytes` turns
   `text.as_bytes().len()` into a build error under `-D warnings`.
3. `cargo fmt --check` is a gate, and a template full of `{{ }}` cannot be
   formatted in place: render a project, `cargo fmt` there, and copy the
   formatted sources back.
4. axum's own 404/405 are plain text. Every route is registered with `any(...)`
   and a `.fallback(...)` so the error bodies stay JSON with the key order
   `error`, then `detail`.
5. `serde_json` emits struct fields in declaration order but `json!` sorts its
   keys — build the responses as structs when the order is part of the test.
6. A non-numeric `/notes/{id}` is a 404 for "no such route", not a 400: parse
   the id in the handler instead of in the extractor.
7. `rows_affected() == 0` is the only honest 404 signal for PATCH and DELETE;
   a `SELECT`-then-write pair races with a concurrent delete.
8. SQLite needs `journal_mode=WAL` and a `busy_timeout`, otherwise two
   connections answer `database is locked` instead of waiting.
