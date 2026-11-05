# {{ title }}

A circuit breaker whose state machine is the product: three states, one probe, a clock you
can move, and counters you can read. It is the other half of a retry policy — retries handle
a blip, a breaker handles a dependency that is *down* and keeps your service from spending
its whole timeout budget waiting to find out.

```bash
uv venv && uv pip install -e . pytest ruff
python -m {{ package_name }} demo
```

```
t=   0.0  call 1 ok               allow closed    closed
t=   0.0  call 2 ok               allow closed    closed
t=   0.0  failure 1               allow closed    closed
t=   0.0  failure 2               allow closed    closed
t=   0.0  failure 3               allow closed    closed
t=   0.0  call while open         deny  open      open, next probe in 30.0s retry_in=30.0s
t=  15.0  half the cooldown       deny  open      open, next probe in 15.0s retry_in=15.0s
t=  30.0  cooldown over           allow half-open half-open, single probe
t=  30.0  call after recovery     allow closed    closed

start     closed
end       closed
verdict   recovered
```

Note what the timeline shows: the third failure is a *successful* call (it was allowed) and
the trip happens after it. That is the point of a breaker — it reacts to what came back, it
does not predict.

Exit codes: `0` the timeline is what the demo claims, `1` it is not (a real regression, and
`demo` is checked in CI), `2` the arguments make no sense.

## Using it

```python
from {{ package_name }}.breaker import Breaker
from {{ package_name }}.model import OpenError

breaker = Breaker(
    failure_threshold=5,      # consecutive failures that trip it
    cooldown_s=30.0,          # how long it stays open
    half_open_successes=1,    # probes that must pass to close it again
    ignore=(ValueError,),     # a caller error is not an outage
)

try:
    body = breaker.call(fetch, url)
except OpenError as refused:
    # we did not call the dependency at all; refused.retry_in says how long
    return cached_response(refused.retry_in)
```

`allow()` / `record_success()` / `record_failure(error)` are there for code that cannot wrap
the call in one function; `call()` is the convenience that keeps the two halves together.

## The traps this stack encodes

1. **Time is a parameter, not a call.** A breaker is mostly a rule about *when* to try again,
   and a test that sleeps through a 30 second cooldown is a test nobody keeps. The clock is
   injected (`Monotonic` in production, `FakeClock` in tests), so the whole state machine —
   cooldown, probe, restart — is exercised in microseconds.
2. **`time.monotonic`, never `time.time`.** A wall clock that steps backwards during an NTP
   correction turns a 30 second cooldown into an hour, or into zero.
3. **Consecutive failures, not a window.** A windowed count lets five failures from ten
   minutes ago trip a breaker for a service that has answered a thousand times since. One
   success resets the count here, and the README says so out loud.
4. **Exactly one probe.** Not "a few": twenty probes is how you finish off a service that was
   just coming up. While the probe is in flight every other caller is refused, and the refusal
   says so.
5. **A failed probe restarts the cooldown.** Otherwise the half-open state re-opens with an
   already-expired deadline and the dependency is retried on every request — the breaker
   becomes a very expensive way to do nothing.
6. **A caller error is not an outage.** `ignore=(ValueError,)` keeps a 422 from tripping a
   breaker on a dependency that is perfectly healthy.
7. **...but an ignored probe failure must release the probe.** A probe that fails with an
   ignored error, and leaves `in_flight` set, jams the breaker half-open forever. It counted
   for nothing, so it must block nothing.
8. **A straggler must not move the breaker.** A request that started before the trip finishes
   after it. Counting that failure would extend the outage for a request the breaker already
   knew about; it is tallied as `late` and ignored.
9. **Refusal has to happen before the network call.** The whole latency win is that an open
   breaker answers in microseconds. `call()` raises `OpenError` without invoking the function,
   and a test asserts the function was never called.
10. **Counters are part of the product.** `stats()` reports requests, allowed, denied,
    successes, failures, ignored, late, trips and probes. A breaker nobody can observe gets
    deleted in the next cleanup, right before the incident that needed it.

## Tests

```bash
python -m pytest        # the state machine, one rule per test
python -m {{ package_name }} selftest   # the same claims, no pytest required
bash smoke.sh           # the CLI contract: exit codes and printed output
```
