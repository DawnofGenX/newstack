# {{ title }}

{{ description }}

A lease is the easy half of a lock: one holder at a time, a deadline, a renewal. The half
that gets left out is what happens to a holder that was *paused* — a GC stop, a suspended VM,
a debugger breakpoint — and comes back after its deadline believing it still owns the thing.
No amount of lease checking on the holder's side fixes that, because the holder's clock and
memory both say it is fine. The fix is a fence: every grant carries a strictly increasing
token, and the resource refuses anything older than the last token it accepted.

## The rules this code keeps

1. **One lease at a time, and the store decides.** A lease is granted only when the current
   one is free or expired, measured on the store's clock. The holder's `valid_at` is a local
   opinion, and `holder_clock_is_irrelevant` exists to name the case where the two disagree.
2. **Every grant is a new token.** Tokens come from a single counter that never goes
   backwards, so "the lease after this one" is always a larger number, releases included.
3. **Renewal extends from now.** `renew` sets `expires_ms = now + ttl`. Extending from the old
   expiry is the bug that pays a paused holder for the time it did not use.
4. **A pause past the deadline ends the lease.** Renewal and release are refused once the
   store's clock is past `expires_ms`; the holder learns by being refused, not by being told.
5. **The resource compares tokens.** `FencedValue.write(token, value)` raises `StaleToken`
   when `token < last_seen`, and the error names both numbers. A resource that accepts writes
   without comparing tokens is `UnfencedValue`, and the demo prints the lost update that
   follows.
6. **One token may write many times.** The fence is a monotonic check, not a write lock: a
   holder does as much work as it likes inside its lease, and only a *newer* lease takes the
   resource away.

## What the demo prints

Real output of `{{ npm_name }} demo` (excerpt):

```
1. a lease alone cannot stop a paused holder; a token can
  the pause is the whole story: worker-a believed it had time left
      0  worker-a acquires          worker-a token 1   until 1000
   1500  clock passes the deadline   expired under worker-a at 1000 (token 1)
   1500  worker-b acquires          worker-b token 2   until 2500
   1500  worker-b writes            accepted: 'b-1' at token 2
   1500  fenced resource            refused: token 1 is older than the last write (token 2): this holder's
   1500  unfenced resource          accepted: 'a-late' at token 1
                                            lease expired and somebody else owns the resource now
  fenced value after the ghost write   'b-1'
  unfenced value after the same write  'a-late'
  the second line is a lost update: the resource had no way to tell
```

`{{ npm_name }} model` prints the same scenario as a table and ends with `contract  kept`,
exiting 1 if the fence ever accepted the stale write.

## Commands

```
{{ npm_name }} demo
{{ npm_name }} model --ttl-ms 1000 --pause-ms 1500
{{ npm_name }} selftest
```

`model` refuses a pause shorter than the lease: if the pause does not pass the deadline there
is nothing to demonstrate, and pretending otherwise would print a table that proves nothing.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the stories ran and the contract held |
| 1 | the fence accepted a write from an expired holder: the contract is broken |
| 2 | the request describes no scenario (zero ttl, a pause inside the lease, unknown command) |

## Layout

```
src/{{ package_name }}/clocks.py     ManualClock: time only moves when you move it
src/{{ package_name }}/lease.py      Lease, LeaseStore, holder_clock_is_irrelevant
src/{{ package_name }}/fence.py      FencedValue, UnfencedValue, StaleToken
src/{{ package_name }}/demo.py       six stories plus the timeline used by `model`
src/{{ package_name }}/cli.py        demo, model, selftest
src/{{ package_name }}/selftest.py   the same promises, checked without pytest
tests/                               pytest versions of those checks
smoke.sh                             real CLI runs, including the failing gates
```

## What this stack does not do

- No network and no coordination service: the store is in-process. What it reproduces is the
  *ordering* problem, which is the part that survives being moved to Redis or etcd.
- No clock synchronisation. The point is that the store's clock decides and the holder's does
  not, so a skewed holder cannot extend its own authority.
- No retry loop. A refused holder is expected to re-read the resource and try again with a
  newer token, which is a decision the caller should make explicitly.
