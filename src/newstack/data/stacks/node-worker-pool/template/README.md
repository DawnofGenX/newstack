# {{ title }}

{{ description }}

Most Node "we moved it to a worker and it got slower" stories are one of four mistakes: a
worker per task, a queue with no bound, a megabyte copied for every message, or a crash nobody
awaited. This stack is a pool that avoids all four, plus the measurements that show each one.

```
{{ npm_name }} bench --size 4 --tasks 64
workers    4
tasks      64
elapsed    19 ms
spawns     4
completed  64
failed     0
refused    0
peak queue 60
sum        2080
contract   kept: a pool of 4 spawned 4, refused 0, failed 0
```

## The rules this stack keeps

1. **A pool spawns once.** `new Worker()` costs about 13 ms on a laptop; 8 tasks with a fresh
   worker each took 102 ms, and 64 tasks through 4 workers took 18 ms. The pool never spawns
   more than `size` workers while it is healthy — `bench` fails the build if it does.
2. **A worker keeps the event loop free.** Three 60 ms CPU tasks in workers left the main thread
   running its 5 ms timer (11 ticks in 61 ms of wall time). The same 180 ms in a busy loop on
   the main thread produced 0 ticks. `async` does not move work off the loop; a thread does.
3. **A transferred buffer is moved, not copied.** Posting a 1 MiB `ArrayBuffer` with a transfer
   list detaches it on the sender (`byteLength` 0) and the worker can hand it back the same way.
   A copy would leave the sender's bytes intact — the detachment is the proof.
4. **A full queue refuses.** `maxQueue` is a bound, not a hint: the rejected `run()` returns a
   `PoolError` naming the depth. A queue that grows without limit turns a slow consumer into an
   out-of-memory kill.
5. **A dead worker is not a finished task.** A task that throws rejects with the worker's own
   message; a worker that calls `process.exit(7)` rejects with *"the worker exited with code 7
   before answering"*. The pool replaces the worker and the next task succeeds.
6. **`close()` drains what it accepted.** Nothing that `run()` resolved to accept is dropped:
   pending tasks finish, then the threads are terminated, and the report says how many
   completed, failed and were refused.
7. **The transfer list travels with the task.** A task that waits in the queue keeps its
   `ArrayBuffer` transfer list, so a queued job still moves its bytes rather than cloning them
   when it is finally dispatched.

## What the demo shows

```
node dist/src/main.js demo
```

Six live stories, none of them constants: reuse against a worker per task, the timer that keeps
ticking, the detached buffer, the bounded queue with its refusal text, the crash and the
replacement, and the close report.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the pool kept its contract (or the command succeeded) |
| 1 | `bench` saw more spawns than `--size`, a failed task, or a refusal |
| 2 | the input was unusable (bad number, missing value, unknown command) |

## Layout

```
src/types.ts    Job, JobResult, PoolStats, CloseReport
src/pool.ts     Pool: idle slots, a bounded queue, replacement, close
src/worker.ts   the worker script: sum, spin, checksum, boom, exit
src/demo.ts     the six stories
src/main.ts     bench, demo, --version, --help
src/selftest.ts offline checks over the pool, the errors and the cli
tests/          node:test suites for reuse, transfers, failures and the cli
```

## What this stack does not do

It does not schedule by priority, split one task across workers, or persist a queue across a
restart. It is the smallest pool that tells the truth about four failure modes, not a job
system.
