# {{ title }}

{{ description }}

A job queue is a promise about what happens to work you have handed over. This one makes
the promise explicit: **at-least-once delivery**, retries on a capped exponential backoff,
and a `dead` state for the jobs that never succeed — never a silent delete. Everything is
one SQLite file, so the queue survives a crash and can be inspected with `sqlite3`.

No runtime dependencies. Python 3.12+.

## Quick start

```console
$ uv venv --allow-existing .venv && uv pip install --python .venv/bin/python -e . pytest ruff
$ .venv/bin/python -m {{ package_name }} push '{"task": "resize", "n": 3}'
8c1d0a1e5b6f49c2a3d4e5f60718293a
$ .venv/bin/python -m {{ package_name }} claim --worker w1
{
  "id": "8c1d0a1e5b6f49c2a3d4e5f60718293a",
  "queue": "default",
  "payload": {
    "task": "resize",
    "n": 3
  },
  "attempts": 1,
  "max_attempts": 3
}
$ .venv/bin/python -m {{ package_name }} complete 8c1d0a1e5b6f49c2a3d4e5f60718293a --worker w1
$ .venv/bin/python -m {{ package_name }} stats
ready=0  leased=0  done=1  dead=0
```

Work the whole queue with a handler of your own:

```console
$ .venv/bin/python -m {{ package_name }} drain --handler myapp.jobs:resize
drained 12 done, 1 retryable, 0 dead, 0 lost
```

## Exit codes

| code | meaning                                                                 |
| ---- | ----------------------------------------------------------------------- |
| 0    | the command did what it says                                            |
| 1    | nothing to claim, or the job you just failed is now dead                |
| 2    | the queue refused the request (bad payload, bad state, lost lease, ...) |

## The traps this stack is built around

1. **`SELECT` then `UPDATE` is not a claim.** Two workers that read the same row and then
   write it both think the job is theirs. The claim here is a single statement whose
   `UPDATE ... WHERE id = (SELECT ... LIMIT 1)` can only match once, inside SQLite's write
   lock. The concurrency check runs 4 threads against 40 jobs and asserts 40 distinct claims.

2. **A lease is a promise with an expiry date.** A worker that dies holding a job must not
   take the job with it, so the row says `leased` until `lease_until` and then becomes
   claimable again. That is also why the attempts counter is incremented *at claim time* —
   a worker that is killed before it can report anything has still used an attempt.

3. **At-least-once means handlers must be idempotent.** A job can legitimately run twice:
   the first worker finished the work and died before `complete`. The queue cannot fix that
   for you; it can only refuse to run the job a third time without saying so.

4. **A long job needs a heartbeat, on a connection created *inside* the heartbeat thread.**
   `process()` starts a thread that renews the lease every `heartbeat_s`. Opening the second
   `Store` in the caller and using it from the thread is not enough: a SQLite connection may
   only be used by the thread that created it, so the store is opened *by* the heartbeat
   thread and closed by it when the job is over. (This is the bug that passes locally and
   raises `ProgrammingError` the first time a handler is slow.) `heartbeat_s` must be well
   below `lease_s`, or the renewal arrives after the expiry it was meant to prevent.

5. **Retries need a ceiling, and the ceiling needs a place to go.** Backoff is
   `min(cap, base * 2 ** (attempt-1))` and there is no jitter, on purpose: a deterministic
   schedule is testable, and a queue that is being hammered by one poison job is exactly
   the case where predictable beats clever. When attempts run out the job becomes `dead`,
   keeps its `last_error`, and is listed by `list --state dead`.

6. **`RETURNING` is what makes the claim atomic *and* legible.** The claim statement writes
   the lease and hands back the row it wrote in one round trip; without it you would need a
   second read and a window in which the row could change.

7. **WAL and a busy timeout, or every writer is an error.** `journal_mode=WAL` lets readers
   work while a writer holds the lock, and `busy_timeout` turns "database is locked" into a
   short wait. Both are set in the constructor, before any statement runs.

8. **`complete()` and `fail()` are conditional writes.** They include `worker = ?` in the
   `WHERE` clause, so a worker whose lease expired cannot mark somebody else's attempt as
   done. A zero rowcount raises; the alternative is a job that silently reports success.

9. **A queue you cannot inspect is a queue you cannot operate.** `stats`, `list --state`,
   and every row keeping `created_at`, `available_at`, `last_error`, `result` and
   `finished_at` exist for the 3 a.m. version of this system.

## Layout

```
src/{{ package_name }}/store.py    the schema, the claim statement, leases, backoff
src/{{ package_name }}/worker.py   process(), drain(), the heartbeat thread
src/{{ package_name }}/cli.py      push / claim / complete / fail / list / stats / drain
src/{{ package_name }}/selftest.py offline checks with a controllable clock
```

## Tests

```console
$ .venv/bin/python -m pytest
$ .venv/bin/python -m {{ package_name }} selftest
$ PY=.venv/bin/python bash smoke.sh
```

The unit tests use a fake clock so a lease can expire without waiting; the two checks that
must use real time (a slow handler outliving its lease) are the only places that sleep.
