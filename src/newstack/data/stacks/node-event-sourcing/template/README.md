# Event store

An append-only event log with optimistic concurrency and replayable projections.

An append-only event log with optimistic concurrency, crash-tolerant loading,
and projections that are provably a function of the log. No runtime
dependencies: Node's own `fs`, `node:test` and `tsc`.

```bash
npm install
npm run build
node dist/src/main.js demo
node dist/src/main.js append --log events.jsonl --stream acct \
  --expected-version 0 --type deposited --data '{"amount":100}'
node dist/src/main.js read --log events.jsonl
node dist/src/main.js project --log events.jsonl --checkpoint accounts.checkpoint
```

## What this stack refuses to do

Most "event sourcing" examples store events. The hard part is what happens
around them, so each rule below is enforced by code and by a test.

**1. An append is atomic, or it did not happen.** Every event in one `append()`
goes into a single JSON line, written with one `writeSync` and one `fsyncSync`.
A crash between two per-event writes would leave half a business fact behind,
and no projection can interpret half a fact.

**2. A torn final line is dropped and counted.** A process killed mid-write
leaves a partial last line. `EventStore.open()` ignores exactly that line and
reports `store.dropped`. A torn line anywhere else means the file was truncated
or edited, so it raises: guessing which records were lost would invent history.

**3. Optimistic concurrency, not last-write-wins.** `append(stream, expectedVersion, events)`
compares the expected version with the stream's current one and throws
`ConcurrencyError` naming both numbers. Two writers that both read "version 3"
cannot both write: one is told to re-read, because silently ordering their
intents would be the store deciding a business question.

**4. Versions are per stream; positions are global.** A version answers "what
did this aggregate know?" A position answers "where in the log am I?" Using a
version as a projection checkpoint needs one number per stream and breaks the
moment a batch spans two streams.

**5. A version hole is an error.** Loading checks that each batch continues the
stream (`fromVersion === current + 1`) and that the range matches its event
count. A log with a hole cannot be replayed, so it is refused at open, not
half-projected.

**6. A checkpoint carries its state.** `{position, state}` is written to one file
and renamed into place, so a resume can never pair one run's position with
another run's state. Catching up from a position with the *initial* state
under-folds the prefix — the tests keep that mistake as a named failing case
rather than a comment.

**7. Projections are pure folds.** `apply(state, event)` may not consult the
clock, the network, or the store. `rebuild()` and `catchUp()` must land on
identical states, and the CLI prints `replay matches a full rebuild` or exits
non-zero. An event with an unknown type is ignored — but its stream is still
recorded, because a projection that silently forgets a stream cannot be
diagnosed later.

## Commands

| command | does |
| --- | --- |
| `append --log PATH --stream NAME --expected-version N --type T [--data JSON]...` | append a batch to a stream |
| `read --log PATH [--stream NAME] [--from N]` | print events and the log position |
| `project --log PATH --checkpoint PATH` | resume a projection, then compare it with a rebuild |
| `demo` | five stories in a temporary log, including a refused stale append |

Exit codes: `0` ok, `1` refused (a stale expected version, or a projection that
diverged), `2` unusable input (bad flag, bad JSON, empty append, damaged log).

## Layout

```
src/types.ts        events, batches, errors
src/store.ts        the append-only log
src/projection.ts   folds, checkpoints
src/demo.ts         an accounts projection and five stories
src/main.ts         the CLI
src/selftest.ts     offline checks over a real log
tests/              node:test suites for the store, the fold and the CLI
smoke.sh            the same contract through a real process and a real file
```

`npm test` runs the suites, `npm run selftest` checks the invariants offline,
`bash smoke.sh` exercises exit codes and the on-disk format.

## Using it for real

- One log file per service, one stream per aggregate. Events are facts; if you
  need to correct one, append a correcting event.
- Keep `apply` free of I/O. If a projection needs data from elsewhere, feed it
  as an event.
- Snapshot large streams: a snapshot is `{position, state}` like the checkpoint
  here, and must be written after the events it covers.
- Deleting or editing a line is not a migration. Write a new event type and
  teach the projection both shapes.
