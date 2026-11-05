# {{ title }}

Half-open integer intervals (`[start, end)`) with the invariants checked by
[Hypothesis](https://hypothesis.readthedocs.io) instead of by hand-written examples.

```bash
uv venv && uv pip install -e . --group dev
.venv/bin/python -m pytest        # examples + properties + a stateful machine
.venv/bin/python -m {{ package_name }} demo
.venv/bin/python -m {{ package_name }} cover 0 2 1 3    # -> 3
```

## Why properties instead of more examples

An example test encodes the cases the author thought of. `coverage([(0, 2), (1, 3)])`
returns `3`, and the interesting bug - summing the lengths and forgetting the merge,
which returns `4` - is invisible until two intervals overlap. Properties state what
must be true for *every* input, and Hypothesis searches for the input that breaks them:

* normalised output is sorted, disjoint and free of empty pieces;
* `coverage` agrees with the size of the point set, and with the oracle that turns
  points back into runs;
* `coverage(left ∩ right) + coverage(left − right) == coverage(left)`;
* `coverage(left) + coverage(right) == coverage(left ∪ right) + coverage(left ∩ right)`;
* normalisation is idempotent.

`CoverageMachine` goes further: it applies random sequences of add/remove rules to
both the interval code and a plain `set[int]`, and compares them after every step.
Sequences are where boundary bugs live, and no single-call example covers them.

## The three settings that keep CI honest

```python
settings(derandomize=True, database=None, deadline=None)
```

* `derandomize=True` - the same inputs every run. A green build stays green, and a
  failure reproduces from the counterexample Hypothesis prints.
* `database=None` - Hypothesis caches failures in `.hypothesis/`. Without this a
  test can pass locally and fail on the runner because the runner has no cache, or
  the other way round because a stale example is replayed.
* `deadline=None` - the default 200 ms budget measures the machine, not the code,
  and a loaded CI box trips it on a test that takes microseconds.

## Shrinking is the feature

`{{ npm_name }} demo` searches exhaustively for the smallest input where a naive
`sum(interval.length)` disagrees with the real coverage, so the answer is stable:

```
smallest input that fools a naive sum: [0, 1), [0, 1)
naive sum 2   real coverage 1
```

`test_shrinking_finds_a_minimal_counterexample` does the same thing at scale with
`hypothesis.find`, which is what turns "some random input failed" into a two-token
counterexample you can paste into an issue.

## Layout

```
src/{{ package_name }}/intervals.py   the half-open interval algebra
src/{{ package_name }}/cli.py         cover / demo / --selftest
tests/test_intervals.py               the documented contract, as examples
tests/test_properties.py              the invariants + the stateful machine
```
