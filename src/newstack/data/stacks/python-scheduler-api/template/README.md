# {{ npm_name }} — a job scheduler

Delayed and repeating jobs with nothing between the process and the database:
a ticker claims what is due, runs it, records the attempt, and decides whether
the job is finished, rescheduled, or has earned a back-off.

    DB_PATH=scheduler.db TICK_SECONDS=0.2 uvicorn {{ package_name }}.main:app --port 8080

## Routes

| Method | Path                 | Answers                                                     |
| ------ | -------------------- | ----------------------------------------------------------- |
| GET    | `/health`            | `{"status":"ok","jobs":N,"due":N}`                           |
| GET    | `/jobs?status=`      | `{"jobs":[…],"count":N}`, ordered by `run_at`                |
| POST   | `/jobs`              | 201 the job; `422 invalid_request` when a field is wrong     |
| GET    | `/jobs/{id}`         | 200 the job; 404 `no job with id …`                          |
| GET    | `/jobs/{id}/runs`    | the attempt ledger, oldest first                             |
| POST   | `/jobs/{id}/run`     | makes it due now — the ticker still does the running         |
| DELETE | `/jobs/{id}`         | 204, and the run history goes with it                        |

A job is `{"name","kind":"count"|"explode","payload","run_at","interval_seconds","max_attempts"}`.
`kind: "count"` runs `wc` over `payload`; `kind: "explode"` always fails, which is
how the retry path is exercised without a fake clock.

## Layout

    src/{{ package_name }}/db.py       pragmas, migrations, one connection per request
    src/{{ package_name }}/jobs.py     claim / finish / execute — all the scheduling rules
    src/{{ package_name }}/worker.py   the ticker thread and its stop
    src/{{ package_name }}/routes.py   the HTTP surface
    src/{{ package_name }}/main.py     lifespan, error envelopes, app factory
    migrations/001_jobs.sql   jobs + runs, with the index the due query needs

## Traps this starter already paid for

- **A SELECT-then-UPDATE claim is not a claim.** With `isolation_level=None` a
  bare SELECT takes no lock, so two tickers read the same due rows and both run
  them. `claim()` wraps the read in `BEGIN IMMEDIATE`; the write lock is the
  serialisation point, and the second ticker simply sees nothing due.
- **Catch up once, not N times.** A job that has been overdue for ten intervals
  owes one run, not ten. Rescheduling from *now* instead of from `run_at` is the
  whole difference between a scheduler and a stampede.
- **Retry needs a cap and a delay.** `attempts` counts failures only, the delay
  doubles from a base with a cap, and the job turns `failed` at `max_attempts`
  instead of spinning forever against a broken handler.
- **`strftime` and `time.time()` are different clocks.** Everything here is a
  float epoch from one clock function so tests can move time without sleeping.
- **`PRAGMA foreign_keys` is per connection.** The delete cascade in `runs` only
  works because every connection turns it on — including the request-scoped ones.
- **A ticker that dies stays dead.** The loop catches everything per tick and
  keeps the error for `/health`; a `RuntimeError` from one job must not stop the
  next job from running.
- **`sleep(tick)` makes shutdown slow.** `Event.wait(tick)` returns the moment
  `stop()` is called, so a signal does not have to wait out a tick.
- **`executescript` commits before it runs.** The migration body carries its own
  `BEGIN … COMMIT` or a half-applied schema gets recorded as done.
