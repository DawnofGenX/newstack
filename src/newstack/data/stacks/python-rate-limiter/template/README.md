# {{ title }}

A token bucket that keeps one integer per key, computes its own `Retry-After`, and forgets keys
that have refilled. No floats, no background sweeper, no guesses.

```console
$ {{ npm_name }} check alice
allow alice        cost=1 remaining=99
$ {{ npm_name }} check alice --limit 2 --per 1 --capacity 3 --repeat 4
allow alice        cost=1 remaining=2
allow alice        cost=1 remaining=1
allow alice        cost=1 remaining=0
deny  alice        cost=1 retry_after=0.500s
$ echo $?
1
```

## The demo, verbatim

```
$ {{ npm_name }} demo
burst 3, then one request every 0.500s

t= 0.000s  three at once (1)         allow client       cost=1 remaining=2
t= 0.000s  three at once (2)         allow client       cost=1 remaining=1
t= 0.000s  three at once (3)         allow client       cost=1 remaining=0
t= 0.000s  one too many at once      deny  client       cost=1 retry_after=0.500s
t= 0.250s  half an interval later    deny  client       cost=1 retry_after=0.250s
t= 0.500s  the next interval         allow client       cost=1 remaining=0
t= 1.500s  a quiet second            allow client       cost=1 remaining=1
t= 3.500s  a full bucket again       allow client       cost=1 remaining=2

stats {'checks': 8, 'allowed': 6, 'denied': 2, 'evicted': 0, 'keys': 1}
```

Read the denials: the second one is `0.250s`, not another `0.500s`, because the wait is derived from
the stored arrival time rather than added to the last failure. That is the difference between a
limiter and a guess.

## Why GCRA instead of a token bucket with a float

A classic implementation stores `tokens: float` and subtracts, then refills by
`elapsed * rate`. Every one of those steps loses precision, and the loss is `O(requests)`; the
bucket you get after an hour of traffic is not the bucket you specified. This one stores a single
integer — the theoretical arrival time (TAT) in microseconds, scaled by the limit so the division
comes last — and derives everything else:

```
interval  = per_seconds * 1_000_000          # one token every interval/limit microseconds
tolerance = (burst - 1) * interval
allow     iff  max(tat, now) + (cost - 1) * interval - tolerance <= now
```

The scaled-integer trick is what makes `--limit 7 --per 60` give a retry of exactly
`8 571 429 µs` instead of `0.8571428571428571` seconds. The arithmetic is in `gcra.py`, and
`selftest` checks the awkward rate explicitly.

## The traps this stack documents

1. **A burst is not a second knob to tune.** `100 a minute` means a hundred at once and then one
   every 0.6 s, or it means one every 0.6 s and nothing else. Both are reasonable; only one is
   what your users experience. `capacity` makes the choice explicit and the printed
   `interval` makes the consequence visible.
2. **A cost above the burst can never be admitted.** That is a configuration error, not a denial —
   saying "retry later" to a request that can never succeed is how a client retries forever.
3. **`Retry-After` is derived, not guessed.** The denial carries the exact instant the request
   could be admitted, rounded up to the microsecond. `retry_after` that is shorter than the truth
   turns a limiter into a retry storm.
4. **`reset_at` is when the bucket is full, not when the next request fits.** Those differ by the
   whole burst, and dashboards want the second one.
5. **Pruning idle keys is what bounds memory.** The table is pruned on write — every
   `prune_every` checks (256 by default), not by a timer — because a key whose bucket has refilled
   is indistinguishable from one that was never seen. `max_keys` is the
   hard ceiling for the case where pruning is not enough (one key per IP, adversarial traffic).
6. **One coarse lock, deliberately.** The critical section is integer arithmetic on a dict — a few
   hundred nanoseconds. Sharding it would trade a real correctness property (a bucket cannot be
   spent twice) for a lock that was never the bottleneck.
7. **The clock is injected.** `FakeClock` makes a minute-long cooldown a test that runs in
   microseconds, and makes the boundary cases (`499_999` denied, `500_000` allowed) exact instead
   of flaky.
8. **`--repeat` is what makes the CLI a gate.** One request can never fail a limit; walking into it
   can. Exit `1` means the limiter said no.

## Exit codes

| code | meaning |
| ---- | ------- |
| `0`  | every request in this run was admitted |
| `1`  | at least one request was denied — this is the gate |
| `2`  | the configuration or the arguments are unusable |

## Commands

| command | what it does |
| ------- | ------------ |
| `check KEY [--cost N] [--repeat N] [--json]` | ask about one key, optionally walking into the limit |
| `simulate --requests N --every MS [--cost N]` | replay a timeline on a fake clock |
| `demo` | a burst, a denial, then recovery |
| `selftest` | the invariants, including 8 threads against one bucket |

All of `check` and `simulate` accept `--limit`, `--per` and `--capacity`.

## Layout

| file | what lives there |
| ---- | ---------------- |
| `src/{{ package_name }}/gcra.py` | the integer state and the arithmetic |
| `src/{{ package_name }}/limiter.py` | the keyed table, the lock, pruning, counters |
| `src/{{ package_name }}/model.py` | `Config` and `Decision` |
| `src/{{ package_name }}/clock.py` | `Monotonic` and `FakeClock` |
| `src/{{ package_name }}/cli.py` | `check`, `simulate`, `demo`, `selftest` |
| `src/{{ package_name }}/selftest.py` | the claims above, as executable checks |

## Quick start

```console
$ uv venv --allow-existing .venv && uv pip install --python .venv/bin/python -e . pytest ruff
$ .venv/bin/python -m {{ package_name }} demo
$ PY=.venv/bin/python bash smoke.sh
```
