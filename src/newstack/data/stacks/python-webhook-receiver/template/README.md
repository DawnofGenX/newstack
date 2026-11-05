# {{ project_name }}

A webhook receiver that trusts nothing it has not signed: HMAC-SHA256 over the raw
request body, a replay window, and a SQLite ledger that turns a retry into a no-op.

## Run it

```bash
uv sync --group dev
WEBHOOK_SECRET_GITHUB=s3cr3t-value uv run uvicorn {{ package_name }}.main:app --port 5480
```

Point a sender at it:

```bash
body='{"kind": "push"}'
ts=$(date +%s)
sig=$(printf '%s.%s' "$ts" "$body" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET_GITHUB" -r | cut -d' ' -f1)
curl -sS -X POST localhost:5480/webhooks/github \
  -H "X-Timestamp: $ts" -H "X-Signature: sha256=$sig" -H 'X-Event-Id: evt-1' \
  -H 'content-type: application/json' --data-binary "$body"
```

`bash smoke.sh` runs the whole contract against a live server on port 5473.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| GET | `/health` | `{"status":"ok","events":N}` |
| GET | `/events` | `{"events":[{"id","source","received_at"}]}` in arrival order |
| POST | `/webhooks/{source}` | `202 {"status":"accepted","id","source","kind"}` |
| POST | `/webhooks/{source}` (retry) | `200 {"status":"duplicate",…}` and no second row |
| POST | `/webhooks/{source}` (bad signature) | `401 {"error":"missing_signature\|missing_timestamp\|bad_timestamp\|stale_timestamp\|bad_signature"}` |
| POST | `/webhooks/{source}` (no `X-Event-Id`) | `400 {"error":"missing_event_id"}` |
| POST | `/webhooks/{source}` (signed, not JSON) | `422 {"error":"invalid_json","detail":…}` |
| POST | `/webhooks/{unknown}` | `404 {"error":"unknown_source"}` |

Secrets come from the environment as `WEBHOOK_SECRET_<SOURCE>` (upper-cased source
name, so `github` reads `WEBHOOK_SECRET_GITHUB`). Nothing else configures them.

## Traps this starter already paid for

1. **The digest is over the bytes that arrived.** `json.dumps(json.loads(raw))` is a
   *different* string — spacing, key order and `\uXXXX` escapes all move — so a
   receiver that parses first and hashes later rejects every honest sender as forged.
   Read `await request.body()` once and verify before anything else looks at it.
2. **Verify before you look at the payload.** The signature check runs before the JSON
   parse, the event-id check and the insert. A body that fails the HMAC never reaches a
   parser, so a malformed payload from an unauthorised sender is a 401, not a 422.
3. **Compare with `hmac.compare_digest`.** `==` on a hex digest returns early on the
   first wrong byte and leaks the prefix length through timing.
4. **Replay window on both sides.** `abs(now - arrived) > tolerance` — a future
   timestamp is as suspicious as an old one, and the tolerance boundary itself is
   accepted (`>` not `>=`).
5. **Idempotency belongs in the database, not in memory.** The event id is the primary
   key; the second insert raises `IntegrityError` and answers 200 "duplicate". A dict in
   the process would forget across a restart, and senders retry precisely after a crash.
6. **`executescript` commits before it runs.** The migration ledger insert travels
   inside the migration's own explicit `BEGIN … COMMIT`, otherwise a half-applied schema
   is recorded as applied.
7. **`check_same_thread=False` plus an explicit isolation level.** Without
   `isolation_level=None` every INSERT opens an uncommitted implicit transaction and
   `close()` throws it away: a 202 for a row that never landed.
8. **Detection marker.** This stack is pinned by the phrase `hmac.compare_digest` in a
   Python file. The database pragma here is spelled `PRAGMA journal_mode = WAL` (with
   spaces) so it does not also fire the `python-fastapi-sqlite` marker — exact-token
   distinctness is what keeps `newstack adopt` unambiguous.
