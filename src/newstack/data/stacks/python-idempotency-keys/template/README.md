# {{ title }}

{{ description }}

A retried `POST /charge` is how a customer gets billed twice. An idempotency key
is the fix, but the useful part is not the table — it is the order of operations,
the lease, and the one window no table can close. This stack implements all three
and measures the number of **effects**, not the number of answers.

## Quick start

    uv venv --allow-existing .venv
    uv pip install --python .venv/bin/python -e . pytest ruff

    .venv/bin/python -m {{ package_name }} request --key order-8f3a1c2d --body '{"amount": 1200}'
    .venv/bin/python -m {{ package_name }} request --key order-8f3a1c2d --body '{"amount": 1200}'

    execute  order-8f3a1c2d       status 201 attempts 1
    replay   order-8f3a1c2d       status 201 attempts 1

The second call never reaches the handler: the first answer is stored verbatim and
returned again. Ask the same key for a different thing and it is refused:

    mismatch   key order-8f3a1c2d was first used for a different request (883003cfc319dec4 != e8a2458098c2bfbe); a key names one intent, and reusing it for another is a bug in the caller

`show` prints the row the decision was made from:

    scope        charge
    key          order-8f3a1c2d
    fingerprint  883003cfc319dec4
    state        completed
    status       201
    body         {"charged": 1200}
    claimed_at   1793911829.7739928
    completed_at 1793911829.774069
    lease_until  1793911829.774069
    attempts     1

## The demo counts effects

    .venv/bin/python -m {{ package_name }} demo

    the same request sent twice                as advertised
      first call   execute  order-8f3a1c2d       status 201 attempts 1
      second call  replay   order-8f3a1c2d       status 201 attempts 1
      the provider was called 1 time(s) for 1200 minor units

    two workers, one key                       as advertised
      worker a: refused, retry in 30.0s
      worker b: execute  order-2b9d7e10       status 201 attempts 1
      the provider was called 1 time(s) for 1200 minor units
      one worker holds the lease while it runs; the other is told to retry

    the same key with a different body         as advertised
      first call   execute  order-51cc0a77       status 201 attempts 1
      second call  refused: key order-51cc0a77 was first used for a different request (affdbb9cf422d58f != 888180eb116593c0); a key names one intent, and reusing it for another is a bug in the caller
      the provider was called 1 time(s) for 1200

    a crash between the effect and the row     as advertised
      attempt 1 charged and then the process died before the row
      the provider was called 1 time(s) so far
      after the lease expired the key was taken over as attempt 2
      the provider was called 2 time(s) for 2400
      nothing in the key table can undo an effect that already happened

    demo: 4 scenarios, 0 not as advertised

The last scenario is the point. The store is not a magic wand: if the effect
lands and the process dies before the answer is recorded, the lease expires and a
retry runs the handler again. What the stack does is make that window small,
visible, and measurable — not deny it exists.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the request executed, or was replayed from the stored answer |
| 1 | refused: another worker holds the key, or the key names a different request |
| 2 | unusable input, or the handler failed (the key is released for an immediate retry) |

## The traps this stack encodes

1. **Claim first, in its own short transaction.** The row is written and committed
   before the handler runs. Holding the SQLite write lock while calling a payment
   provider would serialise every other writer behind a network call.
2. **A key is `(scope, key)`.** The same string on `/charge` and `/refund` is two
   different intents, and a table keyed on the string alone would let one block
   the other.
3. **The fingerprint is canonical.** Retries that reorder JSON members are the
   same request, so a client library upgrade does not turn every retry into a
   conflict; changing the amount is a conflict, because it is a different request.
4. **A lease alone does not fence; the takeover does.** Completing after one's own
   lease expired is allowed as long as nobody else claimed the key — the row still
   says attempt `N`. Only when another worker takes over does the old attempt's
   `complete()` raise `OwnerLost`, which is why the attempt number is the fence.
5. **`busy_timeout` does not cover the `journal_mode` switch.** Two processes
   opening a fresh database at the same moment get `database is locked` from the
   `PRAGMA journal_mode = WAL`, so this store retries that one statement itself
   instead of trusting the busy handler.
6. **A replay is byte-identical.** The success body is stored as text and returned
   as text; re-serialising a parsed dict would quietly reorder keys and change the
   whitespace a client already saw.
7. **The window that cannot be closed.** Effect applied, answer not yet stored,
   process dies. A lease bounds how long the key stays wedged, and the demo shows
   the second charge. Make the handler idempotent, or pass the provider its own
   idempotency key — this table cannot help across that gap.
8. **A failure releases the key immediately.** Otherwise a transient provider error
   makes every client wait out the lease. That is the right trade only because the
   handler is expected to fail before the effect — if it can fail after, the two
   cases are indistinguishable and the retry may duplicate.
9. **Keys must be long and random.** A short or guessable key is a key two clients
   will eventually share, and the failure looks like a mysterious conflict. This
   store refuses anything under 8 characters and anything outside `A-Za-z0-9_-`.
10. **Prune by age.** The table grows by one row per request forever, and rows are
    never reused; deleting completed keys older than the retry window is part of
    the design, not housekeeping.

## Layout

| path | what it holds |
| ---- | ------------- |
| `src/{{ package_name }}/model.py` | `Request`, the fingerprint, `Response`, `Outcome`, the errors |
| `src/{{ package_name }}/store.py` | the table, `claim`, `complete`, `release`, `prune` |
| `src/{{ package_name }}/guard.py` | `execute`: claim, run, complete, or replay |
| `src/{{ package_name }}/demo.py` | four scenarios, each counting effects |
| `src/{{ package_name }}/cli.py` | `request`, `show`, `demo`, `selftest` |
| `src/{{ package_name }}/selftest.py` | 43 checks over the model, the store, the guard and the race |
| `tests/` | 65 tests, including four threads against one key |

## What this is not

It is not a distributed lock and it has no opinion about the handler. Two
processes on different machines sharing a SQLite file is a bad idea, not a
supported deployment; swap `Store` for the same three statements over a real
database and the semantics carry over, but this stack stops at the one file it can
test honestly.
