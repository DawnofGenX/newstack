# {{ title }}

{{ description }}

The bug this stack exists to prevent is a cache that collapses under the load it was
supposed to absorb. A key expires, forty requests miss at the same instant, and forty
loaders run — the cache is now a multiplier for the outage. The fix everyone reaches
for ("put a lock around it") usually produces the second bug: one lock around *all*
keys, so a slow load for `prices` queues every request for `users` behind it.

`SingleFlight` is the third thing: one loader run *per key*, waiters blocked on that
key's own event, and no lock held across the load.

## Quick start

```console
$ uv venv --allow-existing .venv
$ uv pip install -e . pytest ruff
$ python -m {{ package_name }} run --callers 50 --delay 0.1
```

## Fifty callers, one loader

```console
$ python -m {{ package_name }} run --callers 50 --delay 0.1
callers  50, loader delay 0.1s
stats    50 call(s): 0 hit(s), 49 waited, 1 load(s), 0 failure(s)
wall     108 ms; 50 sequential loads would cost 5000 ms
values   1 distinct
```

The loader ran once, forty-nine callers shared that one answer, and the wall clock is
one load rather than fifty. `--json` prints the same numbers for a CI gate:

```console
$ python -m {{ package_name }} run --callers 8 --delay 0.02 --json
{
  "callers": 8,
  "delay_s": 0.02,
  "wall_ms": 30.5,
  "stats": {"calls": 8, "hits": 0, "waits": 7, "loads": 1, "failures": 0},
  "answers": 8,
  "errors": []
}
```

`run` exits `1` if the loader ran more than once — the command is the assertion, not a
demo of one.

## The four scenarios in `demo`

```
thirty callers, one slow loader          as advertised
  loader runs: 1 (calls into the loader: 1)
  waiters served by the same answer: 30
  wall clock: 55 ms, not 1500 ms
  the eighties stampede cost 30 loads; this costs one

a slow key does not block another        as advertised
  a different key answered in 0 ms while the slow load was still running
  slow finished as slow-value
  one registry lock held only long enough to look up a key, not across the load

a failed load is remembered for nobody   as advertised
  callers told the same error: 5 of 5, one distinct message
  loads during the burst: 1; a negative cache would have replayed that failure for a whole TTL
  the next call loaded again: 'recovered'

a TTL starts when the value became readable as advertised
  fresh: 'k-0.0', at 0.9 s: 'k-0.0' (a hit), at 1.1 s: 'k-1.1' (a load)
  an entry that a slow loader would have expired before anyone read it is not a cache, it is a rotation
demo: 4 scenarios, 0 not as advertised
```

## Exit codes

| code | meaning |
| ---- | ------- |
| `0` | one load served the burst, or a scenario held |
| `1` | the loader ran more than once, or a demo scenario stopped being true |
| `2` | the request is unusable: bad key, bad `--ttl`, bad arguments |

## The traps this stack encodes

1. **One lock around the registry, not around the load.** Holding the lock while the
   loader runs serialises every key behind the slowest one — a cache with a queue in
   front of it.
2. **Waiters block on their own key's event.** A single condition variable broadcasts
   to everyone, and all of them wake to re-check keys they never asked for.
3. **A failure is delivered to every waiter and remembered by nobody.** Negative
   caching turns a two-second blip into a TTL-long outage.
4. **Waiters must learn the failure too.** An unset event on the exception path is how
   callers hang forever while the leader has already returned.
5. **The TTL starts when the value became readable.** Start it at the beginning of a
   load that takes longer than the TTL, and the entry expires before a single caller
   reads it.
6. **Expiry replaces the entry, so a waiter never blocks on a finished load.** Creating
   the new entry inside the same critical section is what makes that true.
7. **The value is shared by reference.** Twenty callers get the *same* object; mutating
   it mutates everybody's answer. Copy at the boundary if that matters.
8. **The clock is injected.** TTL behaviour is tested with a `Clock` the test moves,
   never with `sleep`.

## Layout

| path | what lives there |
| ---- | ---------------- |
| `src/{{ package_name }}/model.py` | `Entry`, `Stats`, `FlightError`, key and TTL validation |
| `src/{{ package_name }}/cache.py` | `SingleFlight.get`, `peek`, `forget`, the two locks |
| `src/{{ package_name }}/demo.py` | four scenarios with real threads and a fake clock |
| `src/{{ package_name }}/cli.py` | `run`, `demo`, `selftest` |

## What this is not

It is not a distributed cache. Single-flight is per process: ten pods each run their
own loader for a cold key, and fixing that needs a shared lock (or a stale-while-
revalidate policy), not a bigger lock here.
