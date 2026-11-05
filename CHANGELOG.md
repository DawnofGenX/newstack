# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `python-money-allocation` — money as an integer count of minor units, because a float is how half a cent appears and then does not disappear: `Currency` carries the exponent (JPY 0, KWD 3), `parse('12.345 USD')` refuses a third decimal place until `--round half-even|half-up|down|up` names the loss, a decimal comma is refused instead of being read as a thousands separator, and `Money` has no `__lt__` so `100 JPY` cannot be ordered against `100 USD`. The allocator is largest-remainder on integers — floor every share, hand the leftover units to the largest fractional remainders, ties to the earliest share — and it sums the parts and raises `allocation did not balance; this is a bug, not a rounding error` rather than return a total that disagrees with the input.
- `python-websocket-server` — an RFC 6455 WebSocket service with no dependencies, where the asymmetry is the lesson: client frames must be masked and server frames must not, so the codec takes an explicit `mask=` per direction and a client that forgets it is answered `1002` instead of being read anyway. The handshake answers `404`/`400`/`426` (advertising `Sec-WebSocket-Version: 13`)/`405` before any frame is parsed; fragments are reassembled before the app sees them, control frames may interleave and cannot be fragmented or exceed 125 bytes; text must be valid UTF-8 (`1007`), binary is refused (`1003`), a message over 64 KiB closes `1009`; a close echoes the peer's code and defaults to `1000` while a one-byte or out-of-range payload is `1002`. The smoke test drives real sockets with a masking client and every `curl` carries `--max-time`, because the one assertion that must observe a rejection is exactly the one a broken handshake turns into a hang.
- `python-circuit-breaker` — a breaker whose state machine is the product. Failures are counted consecutively (one success resets them), the cooldown is measured on an injected clock so the whole `closed → open → half-open` cycle is testable in microseconds, and the half-open state admits exactly one probe while every other caller is refused without a network call. A failed probe restarts the cooldown (otherwise the dependency is retried on every request), an ignored error such as a 422 never trips it but does release the probe it occupied, and a straggler that finishes after the trip is tallied as `late` instead of extending the outage.
- `python-task-queue` — a SQLite job queue whose delivery guarantee is the product. `claim()` is one `UPDATE … WHERE id = (SELECT … LIMIT 1) RETURNING …` statement, so two workers cannot win the same row; the lease makes at-least-once explicit (a slow job is re-delivered unless a heartbeat renews it), retries wait `min(cap, base * 2 ** (attempts - 1))`, and a job that runs out of attempts lands in `dead` with its last error rather than disappearing. The heartbeat thread opens its own `Store` inside itself, because a SQLite connection belongs to the thread that created it — the bug that passes every local test and raises `ProgrammingError` the first time a handler is slow.
- `go-consistent-hash`: three in-process cache nodes on a consistent-hash ring (150 vnodes, fmix64-mixed FNV-1a points, replication to the first N owners, ring-order failover, rebalance that moves only the victim's keys) with a `-race` gate and a live HTTP smoke test.
- `go-wal-kv`: an HTTP key/value service with a real write-ahead log (CRC32C frames, fsync before the in-memory map changes, torn-tail truncation on the last segment, tombstones, and compaction via a temporary segment and a rename).
- `python-config-precedence` — layered configuration whose every value carries its provenance. The merge is a fold over `LAYER_ORDER = ("file", "env", "flag")`, so precedence is data instead of a chain of `if`s. Layers are read first and parsed afterwards, which is what lets one run report a bad file value, a typo'd key and a bad `--set` together instead of one per attempt. An unset variable is not an empty one: unset means "no opinion", empty is a value and fails to parse. Environment text is parsed per declared kind, so `bool("false")` never happens, a boolean accepts only real boolean words, and integers go through a regex so `1_000` is refused with a hint rather than silently becoming 1000. Nesting uses `__` because `_` is legal inside a setting name, and a single-underscore variable is reported as the typo it usually is. A configuration printer is a leak, so secrets are masked in `show`, in the JSON payload and in `get` (which refuses without `--reveal`); `check --strict` exits 1 while a secret still holds the default that shipped with the code.
- `python-pytest-plugin` — a pytest plugin whose product is the report. The marker is registered in `pytest_configure`, because `--strict-markers` treats an unregistered decorator as an error and the decorator itself registers nothing. `pytest_runtest_makereport` runs once per phase, so the report keeps `setup`/`call`/`teardown` separately and a failing fixture is recorded as an `error` rather than a failed assertion. Durations are measured around the hook's `yield` and stored in milliseconds. Strict mode raises `pytest.UsageError` at collection and therefore exits 4 before a single test runs. The `summary` command reads the file back with a validated format version, prints the slowest tests, and exits 1 when `--fail-over-ms` is breached.
- **python-mqtt-broker**: an MQTT 3.1.1 broker with no dependencies. The remaining-length field is seven bits per byte with a continuation bit, so a 20 KB payload needs three length bytes; SUBACK is written *before* the retained replay, otherwise a client that reads one reply per call sees a PUBLISH where it expects its grant; `a/#` also matches the parent `a`; a retained publish is only observable from a test at QoS 1 because QoS 0 is never acknowledged and the assertion races the server thread; a connection dropped with unread bytes reaches the peer as `ECONNRESET`, not a clean EOF; and an empty retained publish both deletes the record and delivers an empty message. `mosquitto_pub`/`mosquitto_sub` drive the smoke test.
- `node-cli`: a streaming counter whose contract is the shell — byte-accurate UTF-8, a carried word across chunk boundaries, logical lines, `EPIPE` as exit 0, unknown flags as exit 2, and tests that pipe a real child process into `head`.
- `python-graceful-shutdown`: a SIGTERM path as a tested contract — non-daemon request threads, a drain watcher off the serving thread, the listener closed mid-drain, `503 draining` for keep-alive, a deadline that exits 1 immediately, and a second signal that exits 130.
- `python-rag-eval` — a retrieval evaluation harness whose numbers can be defended. The chunk
  windows are word-aligned with stable `doc#offset` ids and a coverage check, because a step
  larger than `size - overlap` silently leaves a hole and every later metric is then measured
  against an incomplete corpus. BM25 uses the smoothed idf `log(1 + (N - df + 0.5)/(df + 0.5))`
  so a term in every chunk scores zero instead of negative. Before any metric runs, the chunk
  ranking collapses to a document ranking at each document's best chunk — counting chunk hits
  inflates recall for long documents, which are simply chunked more often. Precision divides by
  `k`, not by the number of results returned; a query with no judgements is reported as
  `skipped` instead of being scored 0.0 (which blames the retriever for a gap in the labels);
  macro and micro recall are printed together because either one alone can hide a regression;
  and `compare --baseline before.json --candidate after.json` exits 1 when macro recall, micro
  recall, ndcg or mrr drops, so a retrieval change either earns its place in CI or fails it.
- `python-openapi-client` — the OpenAPI document as an executable contract, not a comment. A
  stdlib-only client reads `fixtures/openapi.json` at run time, validates the request body before
  a byte leaves the process, and validates each response against the schema attached to that
  exact status: an undocumented status is drift, a documented `4xx` is a normal answer whose body
  is checked like any other, and every disagreement is reported at once (`$.tags: expected
  array, got integer`, `$: unexpected member 'server_side'`). `bool` is named before `int`
  because `isinstance(True, int)` is true, so `true` never satisfies an integer schema; path
  values are percent-encoded so `id=a/b` cannot invent a segment; and `validate --operation getNote
  --response saved.json` re-checks a captured body offline with no server anywhere.
- `python-dns-server` — an authoritative DNS server for one zone over UDP **and** TCP on the
  same port: the wire format is hand-written, so the traps are the protocol's. Binding UDP and
  TCP separately with port 0 picks two different ephemeral ports and every TCP client gets
  `ECONNREFUSED`; EDNS0's advertised payload size arrives in the OPT record's CLASS field and
  must raise the datagram ceiling rather than be minimised away; a CNAME belongs in the answer
  before the chain is followed; pointers that do not point backwards are a format error, not a
  loop; TXT rdata is chunked at 255 bytes; and `dig` silently retries over TCP after a
  truncated answer, so a truncation check needs `+ignore` or it asserts the full answer.
- `python-resp-server` — a RESP2 key-value server whose parser is the point: TCP splits a
  command wherever it likes (the reader buffers and only consumes a whole frame, and the selftest
  feeds one command one byte at a time), two commands in one write owe two replies in order,
  inline and multibulk are separate grammars, `*0\r\n` is ignored rather than answered, a
  malformed frame answers one `-ERR Protocol error` and then closes the connection, and `INCR` on
  a non-numeric value must neither answer nor overwrite it. `redis-cli` drives the smoke test, so
  a real client is the judge.
- `python-smtp-sink` — a development SMTP capture server: `Controller(port=0)` does not work
  (aiosmtpd probes the server by connecting to port 0 and raises ConnectionRefusedError), the
  size limit can surface as `SMTPSenderRefused` rather than `SMTPDataError` because EHLO
  advertises SIZE, and dot-stuffing is a wire encoding that must be undone before the message is
  stored — so the test parses the stored mail instead of scanning it for `..`. Messages are
  written to a `.part` file and renamed before the index line is `fsync`ed, and `rebuild`
  recreates the index from the `.eml` files alone because the files are the truth.
- `go-tcp-framing` — a service that is not HTTP: 4-byte big-endian length prefixes in
  front of JSON payloads over raw TCP. The cap is enforced before the length prefix can
  allocate, a zero-length frame is refused instead of read as an empty message, protocol
  errors are answered without dropping the connection, and `Shutdown` closes parked
  clients so Ctrl-C is immediate. The smoke test speaks the byte format from Python
  rather than reusing the server's own encoder, so a framing bug shared by both ends
  cannot pass.
- `python-c-extension` — a CPython extension module built by `setuptools`, with the
  reference implementation kept as the test oracle: `y*` (not `y#`, which refuses a
  `bytearray`) fills a `Py_buffer` so embedded NUL bytes are counted rather than
  truncating the input, `view.len` is copied before `PyBuffer_Release` may clear it, and
  one test asserts that `import` really loaded a compiled `.so` so a future "pure Python
  fallback" cannot pass quietly. Compile flags live in `setup.py` because the
  `pyproject.toml` extension table does not carry them portably.
- `node-http2-api` — an h2c service written straight on `http2`, with no HTTP/1 fallback left
  on by accident: the server listens on the raw `stream` event (the argument to `createServer`
  is the HTTP/1-compatible pair, which is why `stream.respond` is missing there), the body cap
  is enforced while the stream is still arriving, and the contract refuses to pass unless
  `curl --http2-prior-knowledge -w '%{http_version}'` reports `2` rather than a 200 on a
  downgraded connection.
- `node-load-test` — an HTTP load generator plus the thresholds that make it a gate.
  Latency is measured from the instant a request was *due*, not from the instant a socket
  freed up: the second reading is coordinated omission, and it makes a stalled server look
  fast. Percentiles are nearest-rank, so every number is a latency that happened (p95 of
  1..100 is 95, not 95.05) and the method is printed in the report. Warm-up samples are
  excluded *and counted*, durations come from `process.hrtime.bigint()` rather than a wall
  clock that can jump, and every response body is drained - an undrained body never returns
  its socket, so a keep-alive run silently measures connection setup. Throughput is printed
  but never thresholded, because it depends on the machine next to yours. With no
  `--threshold` the run still gates `errorRate <= 0`, and `replay` re-derives the summary
  from an archived sample file with no network, which is what makes the arithmetic testable.
- `latex-paper` — a two-page article built with `latexmk` and `bibtex`, and gated on the PDF
  instead of the sources: `pdftotext` must show the title, every heading, the `[1]` citation and
  the bibliography entry, `pdfinfo` must report two pages, and `build/paper.log` must contain no
  overfull line and no unresolved citation. The starter documents why `\n` inside `\texttt{}` is
  a fatal undefined control sequence, why section numbers vanish from plain `pdftotext` output,
  and why `latexmk -v` hangs a CI step instead of printing a version.
- `kotlin-ktor-api` — Ktor 3 + kotlinx.serialization on JDK 21, one shaded jar. Ktor routes answer
  unknown paths with their own plain-text body, so the service intercepts `Setup` on the raw
  `Application` instead: that keeps `{"error":"not_found","detail":"no route for GET /nope"}`
  byte-exact and makes `/health/` a 404 rather than a rewrite. kotlinx silently accepts
  `"text":42`, so the discriminator between `missing_text` and `invalid_json` comes from a
  hand-rolled scanner, and the shade plugin keeps `ServicesResourceTransformer` (Ktor discovers
  engines through `META-INF/services`) while `dependency-reduced-pom.xml` stays out of the repo.
- `go-trace-api` — a text-stats service that emits W3C trace context without OpenTelemetry or
  any other SDK. The `traceparent` parser is strict (four fields, version `00`, lowercase hex,
  no all-zero ids) and answers `400` instead of silently minting a new root; every response names
  the span that served it; a child span is recorded whose parent is the request span; a trace
  whose sampled flag is `00` still propagates ids but stores nothing; and `/spans` keeps a ring
  of the last 256 spans, reporting how many it evicted. The export is plain JSON, so the whole
  starter is `go vet ./...` plus `go test ./...`.
- `python-property-tests` — half-open interval arithmetic with Hypothesis. The properties are
  the point (`normalize` is idempotent, `coverage` agrees with the point set,
  `coverage(left ∩ right) + coverage(left − right) == coverage(left)`), and `CoverageMachine`
  applies random add/remove sequences to both the interval code and a `set[int]` oracle, which
  is where boundary bugs actually live. Three settings keep CI honest: `derandomize=True`,
  `database=None` (`.hypothesis/` otherwise makes local and runner results disagree) and
  `deadline=None` (the 200 ms default measures the machine, not the code). `demo` proves
  shrinking by searching exhaustively for the smallest input where a naive `sum(length)`
  disagrees - two identical unit intervals, reported as `naive sum 2   real coverage 1`.
- `python-pdf-report` — NDJSON records to a PDF report with reportlab. `rl_config.invariant = 1`
  must be set before the first canvas: it pins the creation date and the object ids, so two
  builds of the same input are byte-identical and a golden-file test is possible. Bytes are
  counted over UTF-8 (a 5-character `héllo` is 6 bytes), text cp1252 cannot encode is replaced
  with `?` and counted, and the finished PDF is read back with pypdf to prove the rows and the
  totals are on the page rather than merely in the summary. Input errors name the line, and an
  exit 2 leaves no half-written file behind.
- `python-migrations` — numbered SQL files applied once, in order, each inside one explicit
  transaction. The ledger keeps the sha256 of every file it applied, so editing a migration
  that already ran fails with `drift` instead of leaving the database and the repository
  quietly different, and a file numbered below an applied one is refused rather than squeezed
  in. Two sqlite3 traps drove the design and are asserted in the tests: `with
  sqlite3.connect(...)` does not roll back DDL, and `executescript` commits any open
  transaction before it runs, so statements are split with `sqlite3.complete_statement` and
  executed one at a time.
- `node-metrics-exporter` — a text-stats service that publishes its own Prometheus metrics without `prom-client`. Counter names must end in `_total`, histogram buckets are cumulative and `+Inf` must equal `_count`, label values are escaped (`\\`, `\"`, `\n`), and the scrape is counted before it renders so it never looks a request behind. `src/exposition.js` is a strict reader for the format — `tools/check_scrape.mjs` runs it over the live payload, so the smoke test fails on a malformed scrape instead of importing garbage.
- `bun-sqlite-api` — a notes API on Bun with no dependencies. `bun:sqlite` has no `db.pragma()`
  helper and `exec("PRAGMA …")` throws the result away, so every connection reads the mode
  back through `query("PRAGMA journal_mode = WAL").get()` and the selftest asserts the value;
  migrations run inside `db.transaction()`, which is synchronous — an `await` inside it commits
  early and leaves half a schema — and `Bun.scanDir` does not exist in 1.4.x, so discovery uses
  `node:fs`. The smoke step stops the process and boots a second server on the same database
  file to prove the rows are persisted and that no phantom row appeared.
- `python-duckdb-report` — a reporting CLI that treats the report as the product, so the numbers
  are exact and the output is diffable. Two rules do the heavy lifting: money is summed as
  `DECIMAL(18, 4)` and never as a binary float (`0.10 + 0.20` is `0.30`, not `0.30000000000000004`),
  and rows whose metric is null are *counted* and printed as `null revenue skipped 1` instead of
  being dropped, because a silent drop turns "sum of revenue" into "sum of the revenue we could
  parse". Groups are ordered by total then by name so two runs over the same file are byte
  identical, and `expected/report.md` is compared with `diff -u` rather than grepped — a table that
  reflows or loses a column fails the build. DuckDB cannot bind an identifier as a parameter, so a
  column or group name has to be interpolated into SQL; `Dataset.column()` is the single gate that
  checks the name against the file's own `DESCRIBE` and returns it quoted (embedded double quotes
  escaped), and `--metric revenu` therefore exits 2 naming the columns that do exist instead of
  raising a binder error. CSV, Parquet and JSON all go through one `READERS` table, and a test
  copies the shipped CSV to Parquet with `COPY … (FORMAT parquet)` to prove both readers agree.
  `smoke.sh` defaults to `.venv/bin/python` when that interpreter exists, so it runs with or
  without `PY` set.
- `python-webhook-receiver` — a webhook endpoint that trusts only signed bytes. The HMAC is
  computed over the body that actually arrived, before any parser touches it: a receiver that
  hashes `json.dumps(json.loads(body))` rejects every honest sender, because spacing, key order
  and unicode escapes all move. Checks run in a fixed order (secret, signature, replay window,
  event id, JSON) so an unauthorised malformed body is a 401 rather than a 422; comparisons go
  through `hmac.compare_digest`; the window rejects future timestamps as well as old ones; and
  the event id is a primary key, so a sender's retry after a crash gets a 200 and no second row.
- `python-batch-inference` — a resumable batch inference runner. The results file *is* the
  checkpoint: it is append-only and flushed per line, a torn final line is discarded on the next
  run, and ids already present are skipped instead of sent twice — so a `kill -9` costs one
  request, not the run. Failures are written as records (`ok: false` plus the reason) rather than
  raised, because a run of 10 000 prompts must not lose its first 9 000 to one 400. Retries are
  limited to 408/429/5xx and network errors with exponential back-off; every other 4xx fails on the
  first attempt, since retrying a malformed request only spends quota. `attempts` sits in each
  record, so a retry is visible in the data instead of buried in a log. Exit codes are the contract:
  0 answered, 1 permanent failure, 2 unusable batch (missing, not JSONL, duplicate ids). It has no
  runtime dependencies, and `tests/stub.py` is a real HTTP server that misbehaves on demand
  (`FAIL429` answers 429 twice, `FAIL400` answers 400 forever), so the retry and failure paths are
  proven against a socket.
- `python-eval-harness` — an offline evaluation harness, and the first stack in the registry that is
  about measuring rather than serving. Three rules are enforced by the code, because each is a way
  published numbers go wrong: a **missing prediction scores zero** (dropping it shrinks the
  denominator and makes a model that answered 3 of 100 look perfect on the ones it answered), the
  metric is written into both the output and the record (`token_f1` and `exact_match` disagree on
  almost everything), and every record carries provenance — the git commit with `+dirty` when the
  tree was not clean. `compare` exits 1 on any per-example regression, so it drops into CI as a
  gate; `--tolerance` is the only way to let a drop through. Predictions can be piped in with
  `--predictions -`, and unknown metrics are rejected by our own code rather than argparse's
  `choices`, because a `SystemExit` from argparse cannot be turned into the documented exit 2.
- `rust-sqlx-api` — axum + sqlx on SQLite, with the schema *in* the binary: `sqlx::migrate!`
  embeds `migrations/`, so a shipped release can never drift from the tables it was built
  against. The macro is gated behind the `macros` feature — `["runtime-tokio","sqlite","migrate"]`
  alone fails `error[E0433]: cannot find migrate in sqlx`, which is the first wall this stack
  hits. Deletes are decided by `rows_affected() == 0` (SQL does not error on a missing row) and
  a non-numeric `/notes/{id}` is answered by the handler as `404 no route for GET /notes/abc`
  rather than by an extractor as a 400. Responses are structs because serde emits declaration
  order while `json!` sorts keys, and `text.len()` — not `text.as_bytes().len()` — is what
  clippy's `needless_as_bytes` insists a byte count is. Its four integration tests open a real
  database file, so the migrator, the pool and the queries are exercised together against a
  temp dir rather than a mock.
- `ruby-cli` — the missing scripting-language CLI, in the shape a gem takes. `bin/{{ npm_name }}`
  is three lines because the whole program is `CLI#run(argv)`: stdin, stdout, stderr and the
  file reader all arrive as keyword arguments, so the suite drives the real CLI through
  `StringIO` and never spawns a process. `Data.define` carries `Counts` and `Options` as
  immutable values, which makes an assertion one comparison instead of three, and the JSON
  body is assembled by hand so the key order is the contract. The counting rules are wc's,
  including the one that trips people up: lines are newline *bytes*, so `"hi"` with no
  trailing newline is one word and **zero** lines. A missing file exits 1 and the remaining
  arguments still get counted; an unknown option raises `UsageError` and exits 2 with only
  the usage line, which is what keeps the two failures distinguishable in a script.
- `actix-web` — the service owns its routing: `web::route()` (actix 4 has no `web::any()`)
  with a manual method check, plus `default_service`, because actix's own `405`/`404` bodies
  are plain text and this stack answers JSON. `serde_json::json!` sorts keys, so a
  byte-compared response has to come from a struct; `query_string()` arrives raw, so `+` and
  `%C3` are the app's job — and the decoder returns `bytes`, because `%C3%A9` is one
  character but two bytes and the counter must see two. Its `detect` rule carries
  `actix-web` as content, which is what keeps a real actix project from coming out
  ambiguous against the bare-`Cargo.toml` Rust stacks.
- `prisma-api` — Prisma 6 + SQLite + Express 5. The CLI resolves `file:./dev.db` relative to
  `schema.prisma`, so the runtime default has to resolve the *same* absolute file or
  `migrate deploy` looks like a no-op against a database the app never opens. `app.all()`
  instead of `app.get()` is what makes an unsupported method a `405` rather than Express's
  own `404`; `express.json()`'s `SyntaxError` is mapped to `422 invalid_json`; and `PATCH`
  only writes the members that were sent, so an untouched `body` survives. The smoke test
  kills the server and asks again, because "the row is in memory" and "the row is in SQLite"
  answer identically until a restart.
- `playwright-e2e` — a browser suite where Playwright owns the server (`webServer`), so
  one command is self-contained; `reuseExistingServer: false` stops a stale process from
  making the suite pass against old code. A project-level `testMatch` alone does not keep
  the desktop project from collecting a mobile-only spec — it reports as "1 skipped" and
  hides a green suite behind a skip, so the desktop project needs `testIgnore`. CI must
  run `npx playwright install --with-deps chromium` (the browser alone lacks libnss3).
- `nuxt-app` — Nuxt 4 SSR app. Without a `pages/` directory Nuxt renders `app.vue` for
  *every* path, so no request is ever a 404; adding `pages/index.vue` is what makes the
  router answer one. `server/api/stats.get.ts` only claims `GET`, and an unmatched method
  falls through to the page renderer as `200` HTML, so the route is one file for every
  method that returns `405` (with `allow: GET`) itself. `tsconfig.json` extends
  `./.nuxt/tsconfig.json`, which does not exist until `nuxt prepare` runs — vitest therefore
  dies with `TSCONFIG_ERROR` on a fresh clone unless `postinstall` prepares the types.
  Vue's `{{ … }}` interpolation cannot be written in the template verbatim (newstack renders
  those), so the page binds with `v-text`.
- `angular-app` — Angular 22 standalone component driven by `signal`/`computed` counters.
  `ng test` runs Vitest in jsdom, so the suite needs no browser and no Karma launcher; the
  built bundle is served by a small static server that has to answer the SPA fallback for a
  deep link and a real `404` for a missing asset, which is what `smoke.sh` checks. `ng build`
  emits a *relative* script `src`, so a bundle check has to add the leading slash. `npm` 11
  warns that `esbuild`'s postinstall did not run, and the build still works — the platform
  binary arrives as an optional dependency.
- `python-litestar-api` — Litestar 2 service. A declared `text: str` handler parameter makes
  Litestar answer `400` with its own envelope before the handler runs, so the handler takes
  `Request` and the contract decides `422`; `request.scope["raw_path"]` already ends with
  `?query`, and appending `query_string` as well counts `"a b?text=a b"`. Litestar answers
  `HEAD` for `GET` routes itself — the catch-all claims it and returns `405`.
- `fastify-api` — Fastify 5 service. Fastify's built-in `application/json` parser takes
  precedence over an added `*` parser, so `{}` arrived as an object and every request
  without a `text` member answered `invalid_json` instead of `missing_text`;
  `removeAllContentTypeParsers()` is what makes the raw body readable. Replies are sent as
  `JSON.stringify(...)` so the key order stays fixed, and parse failures are mapped to 422
  (Fastify would answer 400 on its own).
- `python-scheduler-api` — delayed and repeating jobs with the database as the only
  state. A tick claims due rows inside `BEGIN IMMEDIATE`: a SELECT-then-UPDATE is not
  a claim, because with autocommit on, two tickers read the same rows and both run
  them. An interval job reschedules from *now*, not from its missed slot, so a job
  that has been overdue for ten intervals owes one run rather than ten; failures
  double their delay up to `max_attempts` and then stop, and every attempt lands in a
  run ledger with its counts. The ticker's loop keeps the error of a broken job
  instead of dying with it.
- `node-upload-api` — resumable uploads with no dependencies. The client declares a
  size, then sends byte ranges; an offset that is not what the service already holds
  is a `409` carrying the expected value (accepting it would drop or duplicate bytes
  while the length still looked right), the running SHA-256 is rebuilt from the file
  *before* the next chunk lands so a resumed upload can never hash bytes twice, and
  the index is written through a temp file and a rename so a crash cannot leave a
  truncated ledger next to real bytes. `DELETE` sends no body at all, and `stop()`
  closes idle sockets so keep-alive clients cannot hold the process open.
- `go-jwt-api` — the registry's first stack with accounts. Passwords are
  PBKDF2-HMAC-SHA256 with the iteration count and salt stored inside the digest,
  tokens are HMAC-SHA256 with an absolute `exp` (a duration would be read against
  the wrong clock after a restart), and every rejected token is the same 401
  `invalid_token`: telling "expired" from "forged" hands an attacker an oracle.
  `login` hashes against a dummy digest when the email is unknown so the response
  time does not enumerate accounts, and `/me` looks the account up rather than
  trusting the claims, so deleting a user invalidates a live token. The store
  writes with a temp file, `Sync` and `Rename`; a truncate-then-write leaves JSON
  the next boot refuses to open.
- `python-sse-api` — the registry's first streaming response. `GET /stream` holds
  the connection open and writes one event per tick, `Last-Event-ID` resumes
  instead of replaying, and `src/<pkg>/wire.py` is the only place that knows the
  field format (a newline inside `data:` splits the event, so a multi-line value
  repeats the field name). The `http` step times the first event with a raw
  `http.client` read: curl piped into grep reports the end of the pipe, not the
  arrival of the line, and a server that builds the whole body as one string
  passes every other test.
- `go-worker` — the registry's first batch worker and the first stack with no
  port at all. `job.go` splits failures into permanent (`invalid_json`,
  `missing_id`, `unknown_op`) and `transient`, so only a retryable failure spends
  the retry budget; `state.go` keeps the idempotency ledger and writes it with a
  temp file, `Sync` and `Rename`, because `os.WriteFile` truncates first and a
  kill in between replays the whole input; `worker.go`'s `Consume` runs the scan
  in its own goroutine so a SIGTERM returns without waiting for a producer that
  is blocked in `read(2)`. `run.sh` proves all three: the fixture twice
  (skipped), then an interrupt in the middle of a stream.
- `node-ws-api` — the registry's first non-HTTP service. `ws` runs with
  `noServer: true` and its own `upgrade` handler, because the default
  `new WebSocketServer({ server })` hijacks every upgrade and would accept
  `/anything`; `src/room.js` owns presence and broadcasts join/leave frames to
  open clients only; `tools/contract.mjs` is a live two-client checker, since a
  socket server cannot be exercised in-process the way an HTTP app can.
- `python-fastapi-sqlite` — the registry's first stateful service: FastAPI over
  SQLite with numbered SQL migrations that run in `lifespan` and are recorded in
  a `schema_migrations` table (so a second boot applies nothing), WAL plus a busy
  timeout set per connection, typed request models that reject a blank title, and
  rows that survive a restart. `migrate()` wraps each script in an explicit
  transaction because `executescript` commits before it runs, and the suite
  proves idempotence by applying the migrations twice and diffing `sqlite_master`.
- `kotlin-http-api` — a Kotlin JSON service on the JDK's own `HttpServer`, so the
  only dependency is the standard library. `Counts.kt`, `Json.kt` and
  `Contract.kt` are pure Kotlin (byte-exact counting, a hand-written JSON reader
  that decodes `\u` escapes and surrogate pairs, and the router that owns every
  status code), `Server.kt` is the thin adapter to `com.sun.net.httpserver`, and
  `SelfTest.kt` is the whole suite (50 checks) behind `--selftest` — no JUnit, no
  test runner. Maven shades one runnable jar and the root context means the
  router, not the JDK, answers `404` and `405`.
- `octave-http-api` — an Octave JSON service with no packages to install. Octave
  has no sockets, so `lib/serve.m` drives `java.net.ServerSocket` through the
  bundled JVM bridge, reads the head byte by byte with
  `InputStream.read()` (which returns `-1` at end of stream) and answers with a
  pure-Octave router; `lib/jsonread.m` keeps the last `text` member and decodes
  `\u` escapes and surrogate pairs; `lib/selftest.m` is the entire suite (27
  checks). Octave passes structs BY VALUE, so the JSON reader threads its cursor
  through every helper's return values instead of mutating it in place.
- `fortran-http-api` — a Fortran JSON service with no bindings and no dependencies:
  `server_m.f90` declares `socket`, `bind`, `listen`, `accept`, `recv`, `send` and
  `close` as `bind(c)` interfaces and speaks HTTP/1.1 over an `int8` buffer,
  `counts_m.f90` counts lines/words/bytes over raw bytes, `json_m.f90` decodes
  `\u` escapes and surrogate pairs into UTF-8 (and keeps the last `text` member),
  and `main.f90` adds a `--selftest` mode (38 checks) so `make test` needs no
  framework. The `sockaddr_in` is filled in byte by byte, so there is no struct
  layout to guess, and `SO_REUSEADDR` is set before `bind` so a restart never
  trips over a port still in `TIME_WAIT`.
- `fsharp-http-api` — an F# JSON service on .NET 8 with no web framework. `Server.fs`
  accepts a `TcpListener` connection and reads the head byte by byte until CRLFCRLF
  (`ReadByte()` returning `-1` is the only end-of-stream signal), reads exactly
  `Content-Length` bytes and writes its own status line; `Counts.fs` counts over
  `byte[]` so UTF-8 never round-trips through a decoder; `Json.fs` is a
  recursive-descent reader that re-encodes `\u00e9` and surrogate pairs to UTF-8 and
  keeps the last `text` member; `Program.fs` adds a `--selftest` mode (34 checks, no
  test framework) so the suite runs on plain `dotnet`.
- `sml-http-api` — a Standard ML JSON service on `INetSock.TCP`, compiled by MLton
  into one native binary with `-warnings-as-errors`-grade hygiene and no packages to
  install. MLton's basis has no `Posix.Socket`: the socket is
  `INetSock.TCP.socket ()`, `Socket.recvVec`/`sendVec` take and return `Word8VectorSlice`
  values, and `Socket.Ctl.setREUSEADDR` must be set or the port sits in TIME_WAIT.
  The JSON reader is hand-written (surrogate pairs re-encoded as UTF-8, `\u00e9`
  becomes two bytes), the router is pure, and the harness runs 51 checks without a
  framework.
- `raku-http-api` — a Raku JSON service on Rakudo's own `IO::Socket::INET`, with no
  `zef` and no CPAN: Rakudo ships no JSON parser, so the reader is a small
  recursive-descent parser that keeps a string apart from a number (`{"text": 42}`
  is `422 missing_text`). Three Raku traps are documented in the README: a literal
  space inside a character class is ignored (`/^<[ \t]>$/` never matches a space,
  write `\x20`), `\x0bb` parses as hex `0xBB` (use `\x[0b]`), and a `Nil` from
  `index` cannot be unboxed into an `int`.
- `swift-http-api` — a Swift 6 JSON service on POSIX sockets, built by `swiftc`
  straight from `src/` and `tests/` into one binary: no `Package.swift`, no
  dependency graph, and `-warnings-as-errors` as the gate. The harness is compiled
  into the binary and runs from `--selftest`, so `make test` needs no test framework.
  Two Swift traps are documented in the README because both cost a live run: a
  `String.UTF8View` index is not an `Int`, and `send` through `&out[sent]` ships the
  array's buffer metadata instead of the bytes.
- `java-httpserver-api` — a Java 21 JSON service on the JDK's own
  `com.sun.net.httpserver`, so the whole dependency list is the JDK and a `Makefile`
  over `javac -Xlint:all -Werror`. The JSON reader is hand-written, because the JDK
  ships no JSON API and a number must not pass for a string (`{"text": 42}` is
  `422 missing_text`). `-Werror` also turns a private `RuntimeException` without a
  `serialVersionUID` into a build failure, which is exactly the kind of thing a
  service skeleton should teach.
- `ada-http-api` — an Ada JSON service on `GNAT.Sockets`, with no web framework and no
  JSON library: the counting rules, a validating reader that keeps a number apart from
  a string, and the whole HTTP contract are separate packages, so the 34 checks run
  without opening a socket. Child units live in `textstat-server.ads`, because GNAT
  looks for the dash form and needs the parent `textstat.ads` to exist first.
- `pascal-http-api` — a Free Pascal JSON service on the fcl-web listener, the third
  language in the registry whose service builds on a hand-written JSON reader rather
  than its library's `fpjson`: that reader hands strings back in the system codepage,
  so `\u00e9` would count as one byte instead of two and a surrogate pair would become
  two question marks. Every route is one pure `Route(method, path, query, body)` call,
  so the 58 checks run without a socket, and `make test` is the gate.

- **`haxe-http-api`**: the Haxe service for the eval target (`haxe --interp`,
  no build step, no haxelib). Haxe cannot ask `sys.net.Socket` for
  `SO_REUSEADDR`, so the server drains the connection until the client hangs up
  before closing its own side — otherwise the listening port sits in `TIME_WAIT`
  for a minute and the next run dies with
  `Unix.Unix_error(Unix.EADDRINUSE, "bind", "")` while `ss -ltn` shows it free.
  The JSON reader is hand-written because a number must not pass for a string
  (`{"text": 42}` is `422 missing_text`).
- `cpp-http-api` — C++17 with a plain Makefile instead of CMake: POSIX sockets,
  a validating JSON reader that keeps a JSON number apart from a JSON string, and
  `make test` running a hand-rolled harness.
- `groovy-http-api` — a Groovy JSON service with no build tool: `com.sun.net.httpserver`
  serves a pure route table, `JsonSlurper` already distinguishes a number from a
  string, and the tests are a plain script rather than JUnit.
- `ocaml-http-api` — an OCaml JSON service on the `Unix` module with no opam package
  beyond dune: the JSON reader is hand-written so a number and a string stay
  distinguishable, and `\uXXXX` escapes (surrogate pairs included) decode to UTF-8.
- `d-http-api` — a D JSON service on `std.socket` with a pure route table and
  `std.json` deciding whether `text` is a string; the tests are ordinary `unittest`
  blocks run through `-unittest -main`, so no test framework is installed.
- `c-http-api` — a C11 JSON service on POSIX sockets with no dependencies: the route
  table is a pure function, the JSON reader distinguishes a string from a number, and
  the socket loop sets a read timeout so one stalled client cannot wedge the process.
- `lisp-http-api` — a JSON service on SBCL with no Quicklisp: the route table is a pure
  function, the JSON reader keeps strings and numbers apart (so `{"text":42}` is a
  422 while `{"text":"42"}` counts), and the HTTP loop is `sb-bsd-sockets` with one
  thread per connection.
- `tcl-http-api` — the Tcl service: no tcllib on a stock box, so the JSON
  reader is hand-written (numbers are kept apart from strings, so
  `{"text": 42}` is a 422 while `{"text": "42"}` is counted), the route
  table is one pure function over four strings, and only `src/server.tcl`
  touches a socket. Tcl counts braces textually inside a braced body, which
  is why a `}` inside a quoted string had to be written `\}`.
- `lua-http-api` — the Lua service: LuaSocket plus `cjson` from the
  distribution, 26 checks with no framework, and response documents written
  by hand because a Lua table has no key order to promise. `cjson` is only
  used to read a posted body, so `{"text": 42}` stays a 422 while
  `{"text": "42"}` is counted.
- `guile-http-api` — the Guile service: `(web server)` and `(json)` from
  guile-json, counting over the UTF-8 bytes, the route table as one pure
  procedure tested without a socket, and `set -e` plus an `EXIT` trap so a
  failed assertion stops the server instead of being masked by `wait`.
- `prolog-http-api`, `racket-api`, `powershell-api` — services for the three
  scripting runtimes whose only template so far was a CLI. Each keeps the
  route table in a pure function (a Prolog predicate, a Racket function, a
  PowerShell function) so the tests need no socket, and each flips its CLI
  stack to `detect_fallback` because the CLI marker matches any file of the
  language.
- `haskell-warp-api`, `perl-mojolicious-api` — the last two runtimes that had a CLI stack
  and no service. Both keep the whole route table in a pure function (`Contract.route` /
  `Textstat::Contract->route`) so every status code is pinned by the unit suite and only the
  verify step binds a port. Haskell ships a hand-written JSON reader instead of `aeson` to
  keep the dependency set at warp/wai, and learns that warp hands over the query string with
  its leading `?` still attached. Perl re-encodes a decoded `JSON::PP` value to tell `"42"`
  from `42`, because both stringify the same way and a numeric `text` would otherwise pass.
- `erlang-cowboy-api` — an Erlang JSON service on Cowboy, built with rebar3 and shipped as
  an escript so the run step starts and stops exactly one process. `contract:route/4` is a
  pure function over `(Method, Path, Query, Body)`, so the eunit suites pin every status
  code without a socket and only the verify step binds a port. `rebar.lock` is committed and
  `warnings_as_errors` turns the build into the lint gate.
- `r-plumber-api`: a plumber service in R. The route table is one pure function
  (`textstat_route()`), so the base-R suite pins every status code without binding a
  socket; `bin/serve.R` adds the two things plumber does not default to — an unboxed
  JSON serializer (`{"lines":[2]}` would otherwise be the wire format) and no JSON
  body parser, because plumber answers 500 to a malformed body while the contract
  wants 422 `invalid_json`.

- `mkdocs-site` — an MkDocs Material site over the same counting module family. Two different gates: `mkdocs build --strict` fails on broken internal links and missing nav targets, while `tools/check_fences.py` executes every `python` fence in `docs/` and diffs the printed output against the `# ->` lines beside it, so an example that stops matching the module fails CI. The checker has its own suite that proves it catches a wrong expectation and a traceback.
- `julia-api` — a Julia JSON service on HTTP.jl. `count_text` and `route(method, path, query, body)` are pure functions, so the `Test` suite covers 200/404/405/422 without a socket and only one test opens a port. `ncodeunits`, not `length`, is the byte count; the word scan is a hand-written `isspace` loop because `length` is not defined for the iterator `eachmatch` returns.
- `zig-http-api` — a Zig 0.17 JSON service on `std.http`. `contract.route` is a pure function over method/path/query/body, so the whole status-code surface (200/404/405/422) is tested with no socket, and `counting.zig` is shared with `zig-cli`. Two Zig 0.17 details worth knowing: `std.http.Server.init` takes `Io.Reader`/`Io.Writer` interfaces (the template owns the buffers), and a listener needs `reuse_address = true` or a restart inside a minute fails with `AddressInUse` because the previous socket is still in TIME-WAIT. `build.zig.zon` keeps the fixed `.textstat` identity every scaffolded Zig project ships.
- `gleam-mist-api` — a Gleam JSON service on Mist: `contract.route` is a pure function so the whole HTTP surface is tested without a socket, a gleeunit suite covers it, and the verify step serves the app on a real port. Mist 6 needs `gleam_stdlib` 1.x, which is why the template pins both.
- `scala-cask-api` — a Scala 3 JSON service on Cask: `Contract.route` is a pure function so the whole HTTP surface is covered without a socket, a utest suite covers the counting rules, and the verify step serves a single assembly jar (`scala-cli --power package --assembly`) over a real socket.
- **`crystal-kemal-api`**: Crystal 1.11 + Kemal 1.5 service. As in the Nim stack, the
  counting rules and the route table are pure functions, so `crystal spec` covers every
  status code with no socket and `crystal tool format --check` is a real gate. Three Crystal
  traps are pre-solved: `env.request.body` is an `IO` (`try(&.gets_to_end)`), a `%(...)`
  literal processes escapes so a JSON body must be `%q(...)`, and `JSON::Any#as_s?` is a
  nil-returning cast that must be compared with `nil` — `if node.nil? || node.as_s?` looks
  right but silently accepts an integer. Kemal 1.6 needs a newer Crystal (`Process.on_terminate`),
  so the shard pins `~> 1.5.0`.
- **`nim-http-api`**: Nim service that needs no package manager at all — the counting core
  and the router are plain modules, so `nimble test` exercises every status code through a
  pure `route(method, path, query, body)` function while `std/asynchttpserver` adapts real
  requests to it. Two Nim facts are baked in: `method` is a reserved word (the parameter is
  `httpMethod`), and `std/uri` has no `parseQuery` on 1.6, so the query string is split and
  `decodeUrl`-ed by hand. `requires "nim >= 1.6.0"` must be call syntax in a `.nimble` file;
  the `= @[...]` form fails `nimble build` with "'requires' cannot be assigned to".
- **`clojure-ring-api`**: Ring on `deps.edn`, and the lesson is that a Ring handler is
  already a testable function — `ring.mock.request` builds the request map, so the suite
  covers every route with no port and `ring/ring-mock` sits in the `:test` alias rather
  than the production classpath. `clojure.test` needs a runner to be a CI gate, so
  `run_tests.clj` requires the namespaces and exits non-zero; `ring.util.codec/form-decode-map`
  (not the `parse-query-string` you might expect) parses the query string.
- **`bun-api`**: Bun service whose application is one `(Request) => Promise<Response>`
  function handed to `Bun.serve`, so `bun test` drives the routes in-process while the
  verify step still curls a real socket. Types come from `bun-types` plus `tsc --noEmit`
  (`bun run typecheck`), and `bun install` is a verify step because the toolchain, unlike
  Deno's, resolves its compiler from `node_modules`.
- **`deno-api`**: Deno 2 service with no framework — `handler` is a plain
  `(Request) => Response` function, so `Deno.test` builds requests and awaits
  responses with no port to bind, while `Deno.serve` in `src/server.ts` and a curl
  step in the verify manifest still exercise a real socket. Permissions are least
  privilege: `--allow-env --allow-net` only, so a dependency cannot touch the disk.
  `deno fmt --check` is a gate, which means the template ships already-formatted
  files (`deno fmt` rewraps object literals and generic parameters).
- **`dart-shelf-api`**: the registry's first Dart service, and the shape is worth
  copying: `buildHandler()` returns a `Handler`, so tests call the exact function the
  socket drives — no port, no readiness loop, no flaky `SocketException` on a busy
  runner — while the verify step still boots `dart run bin/<name>.dart` and curls it,
  because a handler that only works in-process fails in production. `dart analyze
  --fatal-infos` (not plain `analyze`) is the gate, and the hyphenated entry file needs
  `// ignore_for_file: file_names`, since a directory name is not a Dart identifier.
  `dart pub get` resolves `shelf` 1.x and `shelf_router` 1.x; the lock file is left for
  you to commit.
- **`grpc-go`**: protobuf-first Go service where the `.proto` is the source of truth. `buf lint` enforces the contract style rules (including the `Service` suffix), `buf generate` builds the stubs locally via `protoc-gen-go`, and the generated code is
  gitignored so a contract and its stubs cannot drift. Tests run over `bufconn` — the real
  gRPC stack without a socket — with one case that dials TCP so listener setup is not
  untested, and the smoke test builds a `probe` client and talks to a live server. Two
  details the suite documents: invalid UTF-8 is rejected by protobuf marshalling before the
  handler sees it, and newer gRPC releases raise the `go` directive, so the module pins
  gRPC rather than floating.
- **`dbt-project`**: analytics engineering where the dataset is the thing under test. A seed
  CSV, a staging view that restores real newlines, and a mart that computes `lines`/`words`/
  `bytes` in SQL — `strlen()` for UTF-8 bytes, `length()` for characters, because DuckDB's
  `length()` counts characters and getting that backwards is the classic analytics bug. A
  singular test encodes the documented numbers and fails the build when a model drifts, and
  `scripts/check_counts.py` re-reads the DuckDB file with no dbt code in the path, so the
  pipeline is checked by something that does not share its code. `+schema` gives each layer
  its own schema (`main_staging`, `main_marts`), which is what makes the mart addressable.
- **`graphql-api`**: schema-first GraphQL on GraphQL Yoga. `src/schema.ts` is SDL, `src/resolvers.ts` resolves it, and `createSchema()` fails at boot if the two drift. Two
  things are worth copying: the depth-limit plugin (`src/limits.ts`) walks the document with
  `visit` and reports `QUERY_TOO_DEEP` *before* execution, so a cyclic client cannot pin a
  worker; and the tests drive `yoga.fetch()` — the exact handler the HTTP server mounts — so
  they test the real pipeline without opening a port. The suite also documents the status-code
  split clients trip over: a malformed request (missing variable) is `400`, a malformed query
  (bad literal, missing argument) is `200` with an `errors` array and no `data`.
- **`openapi-spec`**: contract-first in the literal sense — `openapi.yaml` (3.1, so JSON
  Schema 2020-12) is written before the handler, `spectral` lints it with warnings promoted
  to failures, `redocly` bundles it and renders an HTML reference, and the tests validate
  the server's live responses against the **bundle** with `ajv` in 2020-12 mode. Validating
  the bundle rather than the source is deliberate: a `$ref` that resolves against the source
  can still be broken for the consumer who only has `dist/openapi.yaml`. The server is
  `node:http` with no runtime dependencies, and `additionalProperties: false` everywhere
  means a response that grows a field fails the suite instead of silently widening the
  contract.
- **`sphinx-docs`**: a documentation site whose docs are tested like code. `autodoc` reads
  the docstrings from `src/`, the prose in `docs/guides/counting.rst` is executed as
  doctests, and the build runs with `-W --keep-going` against `nitpicky = True`, so a
  renamed page, an unimportable module or a dangling `:func:` reference fails CI instead of
  publishing a broken site. `tests/test_docs.py` rebuilds the site into a temporary
  directory with `warningiserror=True`, which is the only way to notice that the docs still
  build after a refactor — `sphinx-build` alone would happily reuse a stale `_build/`.
- **`hono-api`**: a Hono JSON API on Node with no bundler — `tsc` emits plain ESM and
  `node dist/server.js` serves it. The stack's argument is the test shape: `createApp()`
  returns the app as a value, so `app.request("/stats?text=…")` hands back a real `Response`
  in-process and the suite needs no port, no server start and no teardown. A missing field,
  a non-string and a non-JSON body are all `422`, an unknown route is a JSON `404`, and the
  verify step still boots the built server and curls it, because a route that only works
  through `app.request()` would pass the unit tests and fail the deploy.
- **`ts-lib`**: a publishable TypeScript package, and the first stack whose subject is the
  *published shape* rather than the code. `countText`/`formatCounts` are ordinary, but
  `package.json` splits `exports` per condition (`import` → `.d.ts`, `require` → `.d.cts`)
  because a single `types` entry lies to CommonJS consumers, and CI proves every declared
  entry point resolves by importing the built ESM file and `require`ing the built CJS one.
  `publint --strict` and `npm pack --dry-run` are verify steps, so a missing `.d.ts` or a
  file outside `files` fails here. TypeScript is pinned to 6.x: the 7.x compiler ships no
  compiler API, which tsup's `.d.ts` bundler needs.
- **`c-cli`**: a C11 command line tool built by plain GNU make, no dependencies. Counting
  lives in a `textstat` library so it is testable on its own, argv parsing is hand-rolled
  (including `--`, a lone `-` for stdin and "later flag wins" like `wc`), and the suite is a
  small `CHECK`/`CHECK_SIZE`/`CHECK_TEXT` header rather than a framework. The build uses
  `-Wall -Wextra -Wpedantic -Werror`, so warnings are failures from the first commit, and
  `make test` plus three shell assertions (exact counts, exit `2` on bad usage, exit `1` on
  an unreadable file) are verify steps.
- **`github-action`**: a JavaScript GitHub Action on `node24` with no dependencies.
  Counting is a pure `countText`, the Markdown table and `GITHUB_OUTPUT` writes live in
  `report.js`, and the `node:test` suite spawns the real entry point with temporary
  `GITHUB_OUTPUT` / `GITHUB_STEP_SUMMARY` files, so what the runner sees is what the
  tests assert — including the exit code for an empty `paths` input.
- **`phoenix-app`**: a Phoenix 1.8 JSON API on Elixir 1.18. A pure `TextStat` module does
  the counting, and endpoint → router → controller → controller test go through
  `Phoenix.ConnTest` with `@endpoint`, covering 200s, 422s and a rendered JSON 404.
  `mix format --check-formatted` is a verify step, so the starter cannot drift from the
  formatter; `elixir-mix-cli` became a detection fallback so a Phoenix project no longer
  matches two stacks.
- **`aspnet-api`**: a minimal ASP.NET Core 8 API. Counting lives in a pure
  `TextStat.Of(string)` returning a `Counts` record, and `WebApplicationFactory` boots
  the real pipeline in memory so routing, model binding, 422s and 404s are tested
  without a port; a live verify step then curls the running binary. `dotnet-cli` became
  a detection fallback so a Web SDK project no longer matches two stacks.
- **`laravel-app`**: a Laravel 13 JSON service on PHP 8.3. Counting lives in a pure
  `App\Support\TextStat` class, `StatController` is a thin route handler, and a PHPUnit 12
  suite proves routing, JSON encoding, the 422 and 404 paths — plus a test that Laravel's
  global `TrimStrings` / `ConvertEmptyStringsToNull` middleware, removed in
  `bootstrap/app.php`, no longer eats the trailing newline that makes a line count wrong.
- **`jsonnet-config`**: a service manifest in Jsonnet where the rules are data too.
  `check` prints `ok` or one line per problem, `render` sorts services and sums
  replicas, and an 18-check suite builds deliberately broken manifests so a validator
  that accepts everything fails the suite instead of passing it.
- **`d-cli`**: D compiled with LDC into one native binary. Counting runs over
  `ubyte[]` so it is byte-accurate, report building sits behind an `Io` struct of
  function pointers so 37 assertions never touch the disk, and a parity suite diffs
  every row against `wc`, padding included.
- **`sml-cli`**: Standard ML compiled with MLton into one native binary. Counting
  runs over `Word8Vector` so it is byte-accurate, argv parsing and report building
  sit behind an `io` record so 37 assertions never touch the disk, and a parity
  suite diffs every row against `wc`, padding included.
- **`haxe-cli`**: a Haxe program compiled to Neko that counts lines, words and
  bytes the way `wc` does. Counting, option parsing and report building live in
  separate modules behind an `Io` interface, so 43 assertions run without touching
  the disk; a parity suite then diffs the output against the real `wc` across six
  inputs and eight flag sets, padding included.
- **`docker-compose-svc`**: a small HTTP service shipped as a container — a
  non-root image with a real `HEALTHCHECK`, a compose file driven by `PORT`, the
  service's answers kept as pure functions so the unit tests need no Docker, and a
  smoke test that builds the image, waits for healthy, checks every answer (health,
  metrics counter, 404, 405, uid) and leaves nothing running.
- **`mdbook-docs`**: an mdBook site whose links and table of contents are
  checked in CI. `tools/check-links.sh` reads every page under `src/`, reports a
  relative link or image whose target is missing, and reports any page that
  `src/SUMMARY.md` does not list — because a page nobody can navigate to is a
  page nobody reads. External, `mailto:` and same-page anchor links are left
  alone; the exit contract is 0 intact / 1 problems / 2 usage error. Twenty-five
  assertions cover the checker, the shipped book, and the two failure modes.
- **`jq-report`**: reports over a JSON access log, written as plain jq programs
  and wrapped in a small shell command. `filters/*.jq` is one report each —
  counts per status, busiest paths, slowest requests, bytes per day, error rate —
  so `jq -c -f filters/top-paths.jq data/sample.json` and
  `run top-paths data/sample.json` cannot disagree. 59 assertions pin every
  answer, the exit-code contract (0 / 1 data / 2 usage), the empty-log case that
  would otherwise divide by zero, and `lint`, which reports a filter that fails
  to compile before any data is involved.
- **`powershell-cli`**: a `wc`-style CLI in PowerShell 7. Counting is a byte loop
  in `lib/TextStat.ps1`, options are parsed by hand in `lib/Options.ps1`, and the
  report lives in `lib/Runner.ps1` — which takes its I/O as a hashtable of
  scriptblocks, so the 57 checks assert the exact bytes on stdout and stderr
  without spawning a process. `main.ps1` is the only file that opens files,
  reads stdin and exits; it decides whether stdin is a stream with
  `stat -L -c %F`, because that is what changes `wc`'s column width.
- **`sqlite-sql`**: not a CLI for once — a SQL reporting project. `schema.sql`
  carries the keys and the `CHECK` constraints, `views.sql` holds the arithmetic
  exactly once, `queries/` is one `SELECT` per report and `bin/NAME` builds a
  throwaway database and prints one of them. 24 assertions cover exact cents,
  every refused row and the `ON DELETE CASCADE` counts; the wrapper never writes
  inside the project.
- **`forth-cli`**: a word-count CLI in plain Forth on `gforth`, no library and
  no build step. Everything is a byte loop over a block the runner reads whole,
  so the counts are exact whatever the file contains; argv is parsed into
  parallel vectors and the rows are padded the way `wc` pads them. 64 unit
  checks in Forth plus 27 shell checks that diff the real binary against the
  host `wc`, including the seven-column pad a pipe gets.
- **`awk-cli`**: a word-count CLI in `gawk` and nothing else. `RS="\0"` makes
  each file a single record, so `length()` is the byte count and two `gsub`
  passes give the line and word counts. The runner fills a report and `main.awk`
  prints it, which lets 69 assertions cover the whole CLI in one process; the
  `stdin` step proves the one path a suite cannot fake, and every row — label,
  padding and `total` — matches `wc` byte for byte, including the seven-column
  pad a pipe gets.
- **`groovy-cli`**: a word-count CLI in Groovy, no build step and no dependency.
  The counting core walks a `byte[]`, the argv parser is a plain list walk, and
  the runner takes its four side effects as closures so the suite drives the real
  logic in-process. 83 assertions plus a five-fixture diff against `wc`.
- **`raku-cli`**: a word-count CLI in Raku. Reading is `Buf`-based, so the
  counting core works on bytes rather than characters; the runner takes the four
  side effects as closures, so a formatting slip fails without spawning a
  process. 82 assertions and a five-fixture diff against `wc`.
- **`guile-cli`**: a word-count CLI in Scheme. Guile's `read-bytevector` is not
  there and `get-bytevector-all` hands back a bytevector, so the counting core
  works on bytes with `bytevector-u8-ref`; the runner takes a record of four
  procedures, so a formatting slip fails without spawning a process. 83
  assertions, `-l/-w/-c` with clusters and `--`, and byte-for-byte agreement
  with `wc`, including the implicit-standard-input row that carries no label.
- **`cobol-cli`**: a word-count CLI in COBOL. GNUCOBOL has no `ARGUMENT-NUMBER` in
  every build, so `main.cob` reads `/proc/self/cmdline` with the same one-byte
  `ORGANIZATION IS SEQUENTIAL` reader it uses for files and splits it on `LOW-VALUE`;
  `TEXTSTAT-COUNTS` counts bytes handed to it a block at a time, `TEXTSTAT-OPTIONS`
  decides what argv means without any I/O, and `TEXTSTAT-RUNNER` is the only program
  that opens anything. One-byte records are what make stdin byte-exact — a pipe and a
  redirect behave alike. The runner reproduces `wc`'s padding and labelling rules and
  keeps the `total` row when an operand could not be read; a directory operand is
  refused instead of being reported as zeroes. A COBOL unit driver (38 assertions over
  the counting and parsing subprograms) plus a shell suite that diffs the built tool
  against the real `wc` add up to `checks: 71, passed: 71, failed: 0`.
- **`bash-cli`**: a word-count CLI written in bash itself — no `wc`, no `awk`, no `od`.
  `lib/counts.sh` counts newlines by substitution, words by a `read -a` split on the
  shell's own whitespace set, and bytes by `${#data}`; `lib/io.sh` is the only file that
  touches the process, and it keeps trailing newlines intact with a sentinel. The runner
  reproduces `wc`'s padding rule (one figure from one operand is never padded, a pipe
  widens every column to seven, otherwise the width is the digits of the bytes read) and
  its labelling rule: a row read from standard input with no operand carries no name,
  while an explicit `-` does. 94 assertions through a hand-rolled harness, `shellcheck -x`
  clean, and the same five-fixture `wc` parity step every CLI stack ships.
- **`hugo-site`**: a Hugo content site rather than a CLI — hand-written `layouts/` and
  partials, no theme and no JavaScript, TOML front matter, a `{{< note >}}` shortcode, and a
  stylesheet that is minified and fingerprinted (with subresource integrity) by Hugo's asset
  pipeline. `make test` renders the whole site into a temporary directory and asserts on the
  HTML — partials ran, the shortcode expanded, headings got ids, the sitemap and RSS feed
  exist, `robots.txt` points at the sitemap, no dev-only script leaked into a built page — and
  it writes deliberately malformed front matter to require the build to *fail*. Six verify
  steps, including a negative one and a real `hugo server` fetch.
- **`pascal-cli`**: a `wc`-style counter in Free Pascal on `fpc` and `make`, RTL only —
  bytes are read raw and folded once, arguments are parsed by hand, and the terminal lives
  behind a record of three function pointers, so the suite drives exit codes and rows
  without spawning a process. 47 assertions, and the shipped workflow checks the suite,
  the exit codes, stdin and byte-for-byte parity with `wc`.
- **`lisp-cli`**: a `wc`-style counter in Common Lisp on SBCL, standard library only —
  bytes are read as `(unsigned-byte 8)` and folded once, arguments are parsed by hand, and
  the program takes a structure of four functions so the suite drives it without a process.
  69 assertions, and the shipped workflow checks the suite, the exit codes, stdin and
  byte-for-byte parity with `wc`.
- **`prolog-cli`**: a `wc`-style counter in SWI-Prolog with no dependencies outside the
  standard library — counting works on a stream, arguments are parsed by hand, output goes
  through two writer closures so the whole contract is testable, and a four-predicate
  harness runs 58 assertions. The shipped workflow checks the suite, the exit codes, stdin
  and byte-for-byte parity with `wc` on five fixtures.
- **`nest-api`**: a NestJS 12 service — a feature module with a controller, a service and a
  pipe that rejects a missing `text` with 400, six unit tests plus four end-to-end tests
  over supertest, and `GET /stats?text=...` returning `{lines, words, bytes}`. NestJS 12
  ships no CommonJS build, so the project is ESM (`"type": "module"`, `.js` import
  suffixes) and `jest.config.js` strips that suffix for ts-jest. The five verify steps
  install, typecheck, test, build and then serve the app and query it live.
- **`octave-cli`**: a wc-style CLI in plain Octave — the counting core, the argument
  parser and the runner live in a `+textstat` package directory, the runner takes its
  environment as a struct of function handles, and a 58-check suite needs no
  framework. The seven verify steps cover the suite, the help text, both exit-code
  paths, standard input, the `-` operand and `wc` parity. Single-quoted Octave strings
  do not interpret escapes, so the fixtures are built with `sprintf`.
- **`ada-cli`**: Ada on GNAT — a counting core that works on bytes, an argv parser with
  `--` and short clusters, and a dependency-free harness of 71 checks; the runner takes
  its two output subprograms as parameters, so only `main.adb` touches the real stdin.
  Eight checks, including a `stdin` step, a `dash-operand` step and byte-exact `wc` parity.
- **`fortran-cli` stack.** Fortran 2018 on `gfortran` and `make`, with no test framework: the counting core takes bytes through a `counter_t`, the runner takes its output units as arguments so the 51-check suite reads what the tool would have printed, and stdin is read a byte at a time through a stream connection to `/dev/stdin` — the only byte-exact option in Fortran.
- **`vhdl-sim` stack** — a synthesizable VHDL counter plus a self-checking testbench on GHDL: every
  check is an `assert ... severity error` and `run.sh` passes `--assert-level=error`, so a wrong design
  is a non-zero exit code rather than a waveform for a human to read. The `inject_fault` generic is the
  teeth test — the shipped workflow runs the testbench a second time with the fault enabled and
  requires that run to fail. `*.vhd` is the detection marker.
- **`deno-cli` stack** — a TypeScript project on Deno, with no `package.json` and no build step: the
  runtime is also the typechecker and the test runner. Counting works on `Uint8Array` so `wc` parity
  holds for UTF-8 and control characters, the argv parser is a pure function, and the runner takes an
  object of four functions so 24 `Deno.test` cases run without touching a file — while the shipped
  `stdin` check still pipes real text through the real command. The wrapper grants only `--allow-read`.
  `deno.json` is the detection marker.
- **`racket-cli` stack** — a Racket project on the core distribution, no packages and no build step.
  Counting works on `bytes` so `wc` parity holds for UTF-8 and control characters, the argv parser is
  a struct with no side effects, and the runner takes a `struct io` of four funs so 54 `rackunit`
  checks run without touching a file — while the shipped `stdin` check still pipes real text through
  the real command. `*.rkt` is the detection marker.
- **`erlang-cli` stack** — an Erlang project on plain OTP and `make`, no rebar and no hex packages.
  Counting works on binaries so `wc` parity holds for UTF-8 and control characters, the argv parser
  is hand-written, and the runner takes a map of four funs (`read_file`, `read_stdin`, `out`, `err`)
  so 42 eunit tests run without touching a file — while the shipped `stdin` check still pipes real
  text through the real binary, because a fake boundary cannot see a broken stdin path. The wrapper
  builds on first use. `Makefile` containing `erlc` is the detection marker.
- **`tcl-cli` stack** — a Tcl project on plain `tclsh`, no package manager and no build step. The
  counting core works on byte strings (`binary scan cu*`) so `wc` parity holds for UTF-8 and control
  characters, the argv parser is hand-written, and the runner takes a dictionary of `readFile`,
  `readStdin`, `out` and `err` so 40 checks run without a process — while the shipped `stdin` check
  still pipes real text through the real binary, because a fake boundary cannot see a broken stdin
  path. `*.tcl` is the detection marker.
- **`rails-app` stack** — Rails 8.1 on Ruby 3.2+: the counting lives in
  `app/services/text_stat.rb` (a plain class, no Rails code), `StatsController` turns it into
  `GET /stats?text=...`, and an `ActionDispatch::IntegrationTest` goes through the router so a
  broken route fails the suite. `bin/setup` writes gems into `vendor/bundle` via the committed
  `.bundle/config` instead of the system gem directory, and the five checks cover install,
  `bin/rails test`, `wc` parity through `bin/rails runner`, and a live request against a
  server started on its own port. No encrypted credentials are shipped.
- **`ansible-role` stack** — a Galaxy-shaped role (defaults, vars, tasks, handlers, templates,
  files, meta, `tests/playbook.yml` + `tests/verify.yml`) that installs a small POSIX counter
  and refuses an unsupported `textstat_columns` value through an `assert`. Fourteen checks
  include idempotence (`changed=0` on the second run), a `--check` dry run that writes
  nothing, and two override runs proving the defaults actually drive the output.
- **`class_name` context key** — a PascalCase identifier (`my-tool` → `MyTool`) for languages
  that name a module after the project; the Rails template uses it for `module MyTool`.
- **`--package-manager NAME`** — the JavaScript stacks declare the managers they are proven
  with (`"package_manager": ["npm", "pnpm", "yarn"]`, npm first) and one value writes every
  command in the project: the install, test, run and build lines in the generated workflow
  and the README, the lockfile name the README asks you to commit, the `cache:` hint for the
  CI setup step, a `Prepare <manager>` step that installs the manager itself, and the
  manager's debug log in `.gitignore`. A manager the stack was not proven with is refused
  before anything is written, and `newstack update --package-manager` moves a project to a
  different one with all of those following.
- **`--node MAJOR`** — the JavaScript stacks declare the majors they are proven on
  (`"node": {"minimum": "22", "versions": ["22", "24"]}`) and one value writes every place a
  version appears: `engines` in `package.json`, the `node-version` matrix in the generated
  workflow, and the README. The floor can only go up and only to a major the stack supports —
  `astro` declares 24 as its own minimum, so `--node 22` is refused instead of scaffolding a
  project Astro refuses to start. `newstack update --node` moves a project's floor later and
  every affected file follows.
- **`newstack stacks outdated`** — which installed stacks have moved upstream, answered with
  one `git ls-remote` per repository rather than a clone, so checking is cheap and writes
  nothing. Exits 1 when a stack is behind or an origin could not be reached; an unreachable
  origin is reported as "could not check" instead of hiding the stacks whose state is known.
  `stacks update` clears it.
- **`newstack stacks update [name]`** — re-pull installed stacks from the repositories they
  came from, so a fix upstream reaches the machine without a manual reinstall. The clone,
  the per-stack validation and the name checks all run before anything is replaced: a
  repository that no longer validates — or one that dropped a stack — leaves the installed
  copy untouched and names what it could not find. A stack whose files did not change is
  reported as already current rather than rewritten. Refreshing a stack updates the
  template; `newstack update <path>` is still what re-applies it to a project, and it keeps
  local edits.
- **`newstack --python 3.12`** — pick the interpreter floor for the Python stacks, and let
  one value write every line that names a version: `requires-python`, the ruff target, the
  trove classifiers, the `python-version` matrix in the generated workflow, the
  `FROM python:` Docker tag and the README's requires line. Each Python stack declares the
  versions it has been proven on (`python` in `stack.json`); the floor can only move up,
  and only to one of them, so `--python 3.9` on `python-cli` or `--python 3.10` on `django`
  is refused before anything is written. Non-Python stacks say the choice does not apply.
  The floor is recorded in `.newstack.json`, so `update` keeps it and `update --python 3.13`
  moves it, rewriting every affected file.
- **`newstack stacks add <git-url>`** — install a stack from any git repository, so a team
  can keep its own starters without forking newstack. `add` clones shallowly, validates
  every stack in the repository (one at the root, one per directory, or under `stacks/`;
  `--dir` picks a subdirectory) before writing anything, refuses a name that already ships
  with newstack, and records where each stack came from in `sources.json`. `stacks remove`
  deletes one, `stacks list` shows origin and revision, and installed stacks are marked
  `[installed]` in `newstack list`, because they are not covered by this repository's CI —
  `newstack check <name>` is the local equivalent. Stacks live in `$NEWSTACK_HOME/stacks`
  (default `~/.local/share/newstack/stacks`). `--force` replaces an installed stack.
- **`--license mit|apache-2.0|bsd-3|none`** on `new` (and `update`, to switch later) —
  the generated `LICENSE` now comes from a licence registry in `data/licenses/` instead of
  a per-template copy, filled in with `--author` and the current year. `none` ships no
  file at all, and the choice is stored in `.newstack.json` so `update` keeps honouring
  it. `adopt` never writes a licence, and `astro` — the one stack whose template had no
  `LICENSE` — now gets one like every other stack. Closes the last roadmap item.
- **`newstack update`** — re-apply a stack's current template to a project `newstack new`
  generated, without losing local edits. `new` now writes a `.newstack.json` record (the
  render context plus a sha256 per file); `update` re-renders the current template with
  the recorded context and merges per file: untouched files are refreshed, edited files
  are reported as conflicts and left alone (exit 1) until you pass `--force`, new
  template files are added, and files the template dropped are reported and only deleted
  with `--prune` — and only while they still match what newstack wrote. `--dry-run` and
  `--json` included. Closes the first roadmap item.
- **`newstack outdated`** — the read-only half of the same comparison: reports which
  recorded files the template has moved past, which files it now adds, and which local
  edits will conflict. Never writes; exits 1 when there is something to pull, so a CI job
  or pre-commit hook can ask "is this project still current?".
- **Two stacks: `bun-cli` and `r-cli`** — `bun-cli` is a zero-dependency Bun +
  TypeScript CLI whose whole test suite is the built-in `bun:test` runner, so a fresh
  clone runs `bun test` offline with no `node_modules` at all; `r-cli` is the same
  wc-style tool in **base R only** (no testthat, no CRAN, no renv) with a hand-rolled
  assertion harness and `Rscript` as the entry point. Both follow the counting-library +
  thin-CLI split and the 0/2/1 exit contract, and both are verified line-for-line against
  real `wc -l -w -c`.
- **`symfony-app` stack** — a Symfony 7 web application on PHP 8.3 + Composer, not a
  console toy: a real kernel with `config/` bundles and routes, a `GET /` route returning
  JSON from an injected pure `TextStats` service, a kernel-booting PHPUnit 11 functional
  test next to the unit test, a working `bin/console`, and a shipped CI workflow with
  PHPUnit plus a console smoke step. Autowiring means the service needs no container
  configuration.
- **`ocaml-cli` stack** — OCaml 4.14 on dune 3.14 with no opam packages at all: pure
  `Counts`/`Options`/`Runner` modules (`(wrapped false)`, no `open` boilerplate in the
  tests), a stdlib-only harness that prints a pass/fail tally and exits non-zero, and a
  shell wrapper around the dune executable so the dashed project name survives dune's
  "executable name must be a module identifier" rule. Verified against `wc -l -w -c` on
  plain, no-trailing-newline, multibyte-UTF-8, empty and control-character files.
- **`helm-chart` stack** — a Kubernetes Helm chart for one stateless HTTP service,
  the first stack that is not a program: named templates in `_helpers.tpl`, a Deployment
  with a hardened `securityContext` and probes, a Service, an optional ServiceAccount,
  and a `values.schema.json` that helm enforces on every `lint`, `template` and `install`
  (so `--set replicaCount=0` fails the chart rather than the cluster). It also ships the
  chart's own `helm test` hook — a pod that curls the Service — and seven checks: lint,
  render, values plumbing, schema rejection, hook rendering, release-name plumbing and
  the hardened defaults, all of which run without a cluster or any plugin.
- **`gleam-cli` stack** — a Gleam 1.19 CLI on Erlang/OTP 27 with no hex packages beyond
  `gleam_stdlib`: pure `Counts`/`Options`/`Runner` modules, a hand-rolled test harness
  (`gleam test` runs the tally and exits non-zero on failure), and one small Erlang module
  for the three things Gleam's standard library has no answer for — argv, stdin and the
  process exit code. `Runner.run` *returns* the 0/1/2 code and only the entry point calls
  `erlang:halt`, so the exit contract is asserted without spawning a process. `gleam
  format --check` is part of the shipped workflow. Verified against `wc -l -w -c`.
- **`scala-cli` stack** — a Scala 3 CLI where the build definition *is* the source:
  `project.scala` holds three `//> using` directives (Scala 3.3.6, main class, munit) and
  there is no `build.sbt`, no `pom.xml` and no build server (`--server=false`, so no Bloop
  daemon is left running). Counting is pure, `Runner.run` takes an `Io` instead of touching
  the world, so the 0/1/2 exit contract and the `wc` column layout are asserted in munit
  without spawning a process. The generated project ships a workflow that installs the
  single scala-cli binary at a pinned version.
- **`haskell-cli` stack** — a GHC 9.4 / cabal CLI whose only dependencies are `base` and
  `bytestring`, both of which ship with GHC, so a generated project builds offline once
  cabal has an index. Counting is a strict `foldl'` over the bytes; `Runner.run` takes an
  `Io` record, so the 0/1/2 exit contract, the `-` stdin label and the `total` row are
  asserted in a 47-check hand-written harness instead of a test framework. `wc` parity is
  a verify step and part of the shipped workflow.
- **Detect rules accept a glob** — a stack marker may be a pattern, so `haskell-cli` can
  be detected by `*.cabal` even though the file is named after the project. Literal
  markers behave exactly as before.
- **`dotnet-cli` stack** — a .NET 8 C# CLI laid out the way a .NET solution actually is:
  a `<name>.sln` with the app project and a separate xUnit project under `tests/`,
  a pure `TextStat` counter that never touches I/O, a hand-written `Options.Parse` that
  returns `{figures, files, status}` instead of throwing, and a `Cli.Run(args, out, err)`
  that *returns* the 0/1/2 exit code so tests assert the contract without spawning a
  process. `-l -w -c` combine like real `wc`, `--` ends flag parsing, and several files
  get a `total` row. Verified against `wc -l -w -c`.
- **`spring-boot` stack** — a Java 21 Spring Boot 3 web service rather than a console
  tool: `StatsService` is pure counting, `StatsController` exposes `GET /stats?text=…`
  (400 when the parameter is missing) and `GET /`, and the JUnit 5 suite covers the
  service directly plus the controller through `MockMvc` — 5 tests, no running server
  needed. A Maven wrapper is included, the jar is `target/<name>.jar`, and the shipped
  workflow runs `mvn -B -ntp verify` plus a live endpoint smoke test on a port the app is
  told to use, so a scaffolded service proves its own HTTP surface in CI.
- **`clojure-cli` stack** — a Clojure CLI tool on `deps.edn` and `clojure -M:test`, with
  no Leiningen and no third-party libraries: `textstat.counts` folds over raw bytes,
  `textstat.options` parses argv by hand, `textstat.cli/run` returns the exit code as a
  value so the `clojure.test` suite (28 tests, 54 assertions) never spawns a process, and
  only `textstat.main` touches the filesystem, `System/in` and `System/exit`. The seven
  shipped checks include stdin, so a broken real-input path cannot hide behind the fake
  I/O record the unit tests inject.
- **`swift-cli` stack** — a Swift 6 CLI on SwiftPM with XCTest and no packages beyond
  the toolchain: `TextStat` is a pure library (`ofBytes` over raw bytes, `add`, the
  right-aligned row layout), `Options.parse` handles `-l/-w/-c`, the long flags, `--`, `-`
  and help/version by hand, and `CLI.run(_:io:)` returns the exit code against a struct of
  closures so 29 XCTest cases never spawn a process. Only `main.swift` touches the real
  files, stdin and `exit`; the wrapper builds in release mode and execs the product. The
  shipped checks include stdin and a `wc -l -w -c` parity loop, and `total` rows follow
  `wc` even when an operand is unreadable.

### Fixed

- **`newstack update` no longer rewrites `.newstack.json` when there is nothing to
  do.** The record carries `updated_at`, so a run over an up-to-date project bumped
  the timestamp and turned "up to date" into a one-line diff every time. The record
  is now written only when something actually changed.
- **`fortran-cli` no longer fails its own test suite on a strict filesystem.** The harness
  used `status='scratch'` units and closed them with `status='delete'`; gfortran on a
  runner refuses with `Fortran runtime error: File cannot be deleted`, so the `test` step
  failed even though the counter was correct. The harness now writes and truncates two
  ordinary files under `build/`, which needs no unlink.
- **The JavaScript stacks pass their tests under yarn, and install under pnpm.** npm and
  pnpm install the peer dependencies a package asks for, yarn 1 does not, so `yarn test`
  failed with `Cannot find module '@testing-library/dom'` (`react-vite-ts`) and with
  `Cannot find package 'vite'` (`next-app-ts`, `node-express-ts`) — projects that were green
  on two managers and broken on the third the new flag offers. Those dependencies are now
  pinned in `devDependencies`, `node-express-ts` allows pnpm to build esbuild
  (`pnpm.onlyBuiltDependencies`), and the pnpm the projects are proven with is pinned to 10 —
  the version CI installs — because pnpm 12 reads build approval from `pnpm-workspace.yaml`
  instead and fails such an install with `ERR_PNPM_IGNORED_BUILDS`.
- **`scala-cli` no longer fails on a cold-cache Maven Central hiccup.** scala-cli resolves the
  pinned Scala version against Maven Central metadata while its cache is empty, and a transient
  failure there is reported as `Cannot find matching Scala version for '3.3.6'` — a version
  that plainly exists. Compilation now retries once (in the manifest's verify step and in the
  shipped workflow), which keeps a genuine compile error failing while a network blip does not.
- **`adopt` recognises a Next.js app as `next-app-ts`.** Every Next project depends on React,
  so the `"react"` marker matched both stacks and `adopt` would only ever have asked for
  `--stack`. `next-app-ts` keeps the specific marker and `react-vite-ts` became a
  `detect_fallback:`, so a Next app resolves to one stack and a plain React project still
  resolves to the Vite SPA; both directions are tested.
- **`adopt` no longer dead-ends on every Composer and Symfony project.** `symfony-app`
  detects `bin/console`, which a plain Composer package does not have, so the generic
  `php-composer-cli` rule became a `detect_fallback:` — a specific marker now wins and a
  bare `composer.json` still resolves to the CLI stack, with both directions tested.
- **Shipped workflows no longer fail their own exit-code steps.** A `run:` step executes
  as `bash -e`, so `./bin/app --bogus …; test $? -eq 2` killed the step on the first
  command and reported the very behaviour the CLI gets right as a failure. The argument
  and missing-file steps in `bun-cli`, `lua-cli` and `r-cli` now capture `$?` under
  `set +e` before asserting it, and a structural test rejects the broken shape across
  every stack.
- **A Haskell project whose name ends in a number now builds.** Cabal reads
  `tool-2024.cabal` as package `tool` at version `2024` and refuses the file, so a project
  generated as `tool-2024` failed before its first build. Templates can now use a
  `cabal_name` context key — the same slug with every all-numeric word given a letter
  (`tool-v2024`) — and `haskell-cli` names its package with it while the executable keeps
  the name the user typed.
- **`astro` no longer fails its own check on a moving Node floor.** `astro check` refuses
  to run below the Node version Astro declares (`>=22.23.4` as of Astro 7.4), and the
  runner image plus the shared CI step still installed 22.23.3, so the astro job failed
  while every other stack was green. The repo's Node step now installs 24, the astro
  scaffold declares `engines.node` and states it in its README, and its shipped workflow
  tests that LTS instead of a floating 22.x.

## [0.4.0] - 2026-11-03

### Added

- **Twenty-four new stacks**, every one shipped with `detect` + `adopt` metadata so
  `newstack adopt` recognises it too. The registry is at 34 stacks.
  - `flask`, `vue-vite-ts`, `next-app-ts` — the web tier: app factory + blueprint,
    Vue 3 + Vite + TypeScript, Next 16 App Router with Tailwind 4.
  - `chrome-extension` — MV3 extension with a Vite build and `npm run pack`.
  - `data-science` — uv + pandas, summarise/clean helpers over in-memory frames.
  - `go-http`, `rust-axum` — real HTTP services with table tests and graceful shutdown.
  - `astro`, `cpp-cmake-cli`, `terraform-module` — static site, C++20 + CMake + CTest,
    and a validated Terraform module whose `terraform test` cases fail on bad input.
  - `ruby-sinatra`, `java-maven-cli`, `php-composer-cli`, `csharp-cli`,
    `elixir-mix-cli`, `dart-cli` — JSON API on Sinatra, and five CLI stacks spanning
    Maven, Composer, .NET, Mix and pub.
  - `kotlin-cli`, `zig-cli`, `julia-cli`, `nim-cli` — four more ecosystems with no
    package manager between them: Kotlin on Maven (Gradle's wrapper jar cannot be
    templated), Zig with in-source test blocks, Julia on stdlib `Test`, and Nim on
    `unittest`.
  - `perl-cli`, `lua-cli`, `fsharp-cli`, `crystal-cli` — four ecosystems that gate with
    no package install at all: Perl on core-module `Makefile.PL`, Lua 5.4 with a
    hand-rolled spec harness, F# on .NET 8 with a discriminated-union parser, and Crystal
    with `crystal spec` and zero shards.
- **One counter-persistence contract** across the five user-facing JS stacks: state is
  stored under the key `newstack:counter`, clamped to a non-negative integer, and a
  storage failure degrades to memory. Svelte and Next restore in `onMount`/`useEffect`
  so server rendering cannot produce a hydration mismatch.
- **The Chrome extension reports whether it is active on the current page**, instead of
  leaving the user to guess.
- `newstack adopt` guides the user to review a diff instead of printing scaffold
  next-steps that would run the demo.

### Changed

- Template rendering happens fully in memory first, so a template error writes nothing.
- `--name` is now sanitised against Java's reserved words as well as Python's: `--name
  static` used to render `package static;`, which no Java compiler accepts.
- The registry no longer validates every stack on load: a half-built stack directory is
  reported by `list` and `check --all` instead of breaking them.

### Fixed

- Shipped Crystal workflows pin `crystal-lang/install-crystal@v1.9.5` instead of `@v1`:
  that action publishes exact tags only, so a moving major resolved to nothing and the
  job died before its first step. The bare-major guard in the test suite now covers every
  action known to be in that category instead of `astral-sh/setup-uv` alone.
- Shipped Node workflows no longer use `actions/setup-node` with `cache: npm` while the
  template has no lockfile — that fails inside the setup action before any install runs,
  and only a real runner proved it. A regression test now fails if any shipped workflow
  needs a file the template does not ship.
- `data-science` summarised across mixed units (counts and revenue averaged together);
  it now reports per-column means, and the tests assert the meaningful number.
- Accessibility and copy pass over the six user-facing templates: focus moves to the
  target of an in-page scroll, counters are announced through `role="status"`, controls
  name their action rather than their state, and `:focus-visible` is styled everywhere.


## [0.3.0] - 2026-11-02

### Added

- **`newstack adopt <dir>`** — retrofit a stack's infrastructure onto a project that already
  has code. Additive by construction: an existing file is never opened for writing, and any
  change that would need a merge inside a file is reported as a manual step instead.
  - Auto-detects the stack from the project's own markers (`go.mod`, `Cargo.toml`,
    `manage.py`, `pyproject.toml`/`package.json` contents, a bare `index.html`); ambiguous
    matches print candidates and exit 2; `--stack` overrides.
  - Copies infrastructure only — workflows, `.gitignore`, lint/type config — never a
    README, LICENSE, `pyproject.toml`, `package.json`, `go.mod` or source file.
  - `--dry-run` reports without writing; re-running is a no-op; `--json` for scripting.
  - `--with-tests` (experimental) also copies the stack's starter tests.
- Manifest keys `detect`, `detect_fallback`, `adopt` and `adopt_tests`, validated by the
  registry and by tests that require every adoptable path to exist and to be infrastructure.

### Changed

- `newstack new` and `adopt` share one step formatter, so an unknown `{placeholder}` in a
  manifest's `next_steps` prints literally instead of raising `KeyError`.

## [0.2.0] - 2026-11-02

### Added

- Four new stacks, all verified the same way as the original six:
  - `go-cli` — stdlib `flag` parsing, table tests, vet/test/build gates.
  - `rust-cli` — std-only parsing, lib+bin split, fmt/clippy/test/release gates.
  - `django` — Django 6.1, config/core split, SQLite, pytest-django, and a
    migration-drift step that fails when a model changes without a migration.
  - `svelte-kit-ts` — SvelteKit 3 with Svelte 5 runes, Vitest, static adapter build.
- CI runs one job per stack (ten in total), with Go and Rust toolchains installed only
  for the jobs that need them.
- Docs drift tests: the README table and the CI matrix must both list every registered
  stack, and the README may not hardcode a stack count.

### Changed

- Install instructions now point at PyPI (`uvx newstack`, `uv tool install newstack`).

## [0.1.0] - 2026-11-02

### Added

- `newstack new <stack> <path>` — render a stack, initialise git, first commit.
- `newstack new … --github [OWNER/REPO]` — create the GitHub repository and push.
- `newstack list` — every stack with its toolchain requirements, `--json` supported.
- `newstack check <stack…> | --all` — generate into a temp dir and run the stack's own
  verification steps (`install`, `lint`, `test`, `build`), reported per step.
- `newstack doctor` — which toolchains are installed, which stacks can be verified here.
- Six stacks: `python-lib`, `python-cli`, `fastapi`, `react-vite-ts`, `node-express-ts`,
  `static-site`.
- Stack registry is extensible through the `NEWSTACK_STACKS` environment variable.
- Zero runtime dependencies: standard library only.
