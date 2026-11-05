# {{ title }}

{{ description }}

Two retry policies can be five lines apart in a code review and behave nothing
alike under load. This stack measures the difference instead of arguing about it:
200 clients hit one server that is down for a second, and every policy is scored
on the same outage with a virtual clock.

```console
$ {{ npm_name }} simulate --policy full-jitter --clients 200 --max-peak 60
policy       full jitter over 100 ms x2 cap 1000 ms
clients      200 (seed 7, down until 1000 ms)
attempts     1210 (1010 of them retries)
peak retries 34 in the 10 ms bucket at 90 ms
buckets      179 carried a retry
delays       mean 265.7 ms, longest 995.5 ms
settled      all clients by 1979 ms
gate         peak 34 <= 60 ok
```

## The rules this code keeps

1. **The retry is bucketed by when it arrives, not by when it failed.** A wave
   is what the server sees. Bucketing by failure time puts every policy's peak
   at the client count and measures nothing.
2. **A backoff is not jitter.** `exponential` waits longer each time and still
   sends all 200 clients back together; only the interval between waves grows.
3. **Jitter spreads the wave.** `full jitter` draws uniformly below the
   exponential ceiling, `equal jitter` keeps the lower half, and both trade wall
   clock time for a smaller peak — a trade this stack prints rather than hides.
4. **The pile-up and the retry count are different questions.** `decorrelated`
   makes fewer retries than `exponential` *and* a peak of 15 against 200; a
   policy can improve one and worsen the other.
5. **Decorrelated jitter is not monotone.** It draws from the previous wait, so
   its sequence can shorten — that is the design, not a bug, and the demo counts
   the decreases.
6. **Determinism is part of the measurement.** The generator is SplitMix64, not
   `random.Random`, so a published curve reproduces exactly on any Python.
7. **A gate is a number.** `--max-peak N` exits 1 when more than N retries land
   in one bucket, so a policy regression fails a build instead of a review.

## Same outage, five policies

```console
$ {{ npm_name }} compare --clients 200
policy                                    peak  buckets  retries   settled
fixed 100 ms                               200       10     2000      1000
exponential 100 ms x2 cap 1000 ms          200        4      800      1500
full jitter over 100 ms x2 cap 1000 ms      34      179     1010      1979
equal jitter over 100 ms x2 cap 1000 ms     48      130      831      1976
decorrelated 100 ms cap 1000 ms             15      173      712      1993
pile-up      200 simultaneous retries against 34 (5.9x lower)
cost         979 ms of extra outage for the calmer wave
```

`fixed` and `exponential` both peak at the full population. `full jitter` cuts
the peak 5.9x and pays 979 ms for it. `decorrelated` retries less often *and*
spreads wider, which is why it is often the default in practice.

## The six stories

```console
$ {{ npm_name }} demo
1. a delay without jitter keeps the population synchronised
  policy           peak  buckets  retries   settled
  fixed 100 ms      200       10     2000      1000
  exponential       200        4      800      1500
  the first wave is unavoidable: 200 clients learn of the outage at once
  the second wave is a choice: fixed sends 200 back together, exponential still sends 200
  -> holds

2. jitter spreads the same clients over many more buckets
  policy           peak  buckets  retries   settled
  fixed 100 ms      200       10     2000      1000
  full jitter        34      179     1010      1979
  equal jitter       48      130      831      1976
  full jitter cuts the peak 5.9x while retrying 1010 times against 2000
  -> holds

3. the calm is paid for in wall clock time
  fixed        calm no, settled   1000 ms
  full jitter  calm yes, settled   1979 ms
  the premium is 979 ms of extra outage for 166 fewer simultaneous retries
  a policy that hides this trade is selling one number and hiding the other
  -> holds

4. the number of retries and the size of the wave are different questions
  policy           peak  buckets  retries   settled
  exponential       200        4      800      1500
  decorrelated       15      173      712      1993
  decorrelated retries 88 fewer times than exponential and its peak is 15 against 200
  fewer retries is not less strain: the two numbers move independently
  -> holds

5. only decorrelated produces a non-monotone sequence
  exponential   100, 200, 400, 800, 1000, 1000 ...
  full jitter   39, 3, 360, 466, 452, 249 ...
  decorrelated  178, 107, 300, 566, 823, 691 ...
  waits that got shorter: exponential 0, full jitter 11, decorrelated 4
  decorrelated looks at the previous wait, so its sequence is not a backoff at all
  -> holds

6. the same seed reproduces the same curve
  seed 7      peak   34, retries  1010, settled   1979 ms
  seed 7 again peak   34, retries  1010, settled   1979 ms
  seed 8     peak   32, retries  1017, settled   1909 ms
  the generator is SplitMix64, so a published curve can be reproduced exactly
  -> holds
```

## Use it in a test suite

```python
from {{ package_name }}.policies import FullJitter
from {{ package_name }}.simulate import simulate

result = simulate(FullJitter(100.0, 2.0, 1_000.0), clients=200, fail_ms=1_000.0)
assert result.peak_retries < 60, result.lines()
assert result.completed
```

`simulate()` is pure: a virtual clock, a heap, and one `Rng` per client, so the
assertions above hold on every machine and every run.

## Exit codes

| code | meaning |
| ---- | ------- |
| `0` | answered; with `--max-peak`, the peak is inside the limit |
| `1` | answered, and the pile-up breached the limit (a data-quality gate) |
| `2` | the question could not be asked: unknown policy, zero clients, zero bucket |

## Layout

```
src/{{ package_name }}/
  rng.py        SplitMix64, so the curves reproduce
  policies.py   fixed, exponential, full jitter, equal jitter, decorrelated
  simulate.py   the virtual clock, the heap, the per-bucket pile-up
  demo.py       the six stories above
  cli.py        simulate, compare, demo, selftest
  selftest.py   checks that need no test runner
tests/          45 pytest cases
smoke.sh        the CLI contract, end to end
```

## What this stack does not do

It does not model a network, a load balancer, or a partially failing service: the
outage is one interval and success is a timestamp comparison. It also does not
recommend a policy — it makes the trade visible, and the choice stays yours.
