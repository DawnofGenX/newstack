# {{ npm_name }}

An actix-web 4 text-statistics service on `127.0.0.1:5462`: two routes, a JSON
contract that is byte-checked by a live smoke test, and 39 offline self-checks
that need no socket.

## Contract

| Request | Reply |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /stats?text=...` | `200 {"text":..,"lines":N,"words":N,"bytes":N}` |
| `POST /stats` `{"text":".."}` | same 200 shape (key order: text, lines, words, bytes) |
| `POST /stats` no `text` member | `422 {"error":"missing_text"}` |
| `POST /stats` non-string `text` / malformed JSON | `422 {"error":"invalid_json"}` |
| wrong method on `/health` / `/stats` | `405 {"error":"method_not_allowed"}` |
| unknown path | `404 {"error":"not_found","detail":"no route for <METHOD> <PATH>"}` |

Counting is `wc` semantics over raw UTF-8 bytes: lines = `0x0A` count; words =
maximal runs of bytes outside `{20 09 0A 0D 0B 0C}`; bytes = UTF-8 length.
`"a b\n"` = 1/2/4 - `"héllo wörld\n"` = 1/2/14 - `"a b\nc\n"` = 2/3/6 - `""` = 0/0/0.

`PORT` overrides the port (default 5462); a non-numeric `PORT` exits 2.

## Layout

```
Cargo.toml          edition 2021; bin and lib both named {{ npm_name }}
Cargo.lock          committed, so CI resolves the same graph every run
src/counts.rs       wc-semantics counter (byte level)
src/contract.rs     dispatch(): the single place that decides status + body
src/routes.rs       actix handlers; any-method routes so 405s are our JSON
src/lib.rs          route table + run()
src/main.rs         entry point, PORT parsing, `--selftest`
tests/selftest.rs   cargo test mirror of the suite
Makefile            build / test / selftest / serve / smoke / clean
bin/{{ npm_name }}  755 wrapper -> target/release/{{ npm_name }}
smoke.sh            live curl contract; starts and stops its own server
```

## Traps this starter already paid for

1. **`web::any()` does not exist in actix-web 4.** The any-method builder is
   `web::route()`; `web::any()` is `E0425: cannot find function 'any' in module 'web'`.
2. **Handlers passed to `.to()` must be `async fn`** in actix-web 4 - a sync
   `fn(HttpRequest) -> HttpResponse` fails `E0277: Handler not satisfied`.
3. **Route registration order is match order.** A catch-all `web::route()` on
   `/stats` registered before the specific POST route swallows the POST.
4. **actix's built-in 405/404 bodies are plain text.** To answer JSON you must
   own the routes (`web::route()` + manual method checks) *and* set
   `default_service`; the defaults cannot be decorated.
5. **`serde_json::json!` output is key-sorted** (`detail` before `error`), so a
   byte-compared body must be built from a struct - serde emits struct fields in
   declaration order. `StatsReply` exists for that reason.
6. **`+` is a space only in a query string, and actix hands you `query_string()`
   raw** - you percent-decode it yourself. A truncated escape (`%C`) and a bad
   one (`%zz`) are both malformed; `%C3` is a *valid* prefix.
7. **`cargo build | tail` hides the exit status** - the pipeline reports
   `tail`'s. Run the build bare in CI, or with `set -o pipefail`.
8. **A killed server leaves the port for the next run.** `smoke.sh` refuses to
   start when something already answers `/health`, and its `EXIT` trap reaps the
   child so the port is free when the step returns.

## Run

```sh
cargo build --release
./target/release/{{ npm_name }} --selftest   # 39 checks, no server needed
cargo test                                   # same invariants under cargo test
bash smoke.sh                                # live contract, stops its own server
```
