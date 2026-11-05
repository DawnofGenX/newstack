# {{ title }}

{{ description }}

A sketch trades memory for accuracy, and the only honest way to ship that trade is to print
both halves of it. This one answers "how many times did this item arrive?" from `width x
depth` counters, and every answer comes with the error it may carry. The estimate can be
wrong in exactly one direction — collisions add to a counter, never subtract — so the number
is an upper bound, and the overestimate is at most `e / width` of the updates.

## The rules this code keeps

1. **No underestimates, ever.** `add` only ever increments. A test streams 125,652 updates
   through a 256x5 sketch and asserts the count of estimates below the truth is zero.
2. **The promise is printed beside the number.** `estimate` prints the item's count and
   `e/width * updates`; the demo compares the largest real overestimate against that bound.
3. **Width buys accuracy, depth buys confidence.** `e/width` is the row bound and
   `exp(-depth)` is the failure probability; `info` shows both, so a wide-but-shallow sketch
   cannot be mistaken for a safe one.
4. **Depth comes from one digest.** A blake2b digest is at most 64 bytes, so at most 8 rows
   can be sliced from one hash. `depth > 8` is refused rather than quietly wrapping around.
5. **Merging is pointwise addition.** The sketch of two streams' union is the sum of their
   sketches, and the demo proves the merged rows equal a single pass over the concatenation.
6. **Conservative update is a measured win, not a slogan.** It touches only the counters that
   already hold the minimum; on the same stream it lowered the mean overestimate from 34.87
   to 11.39 at 256x4.
7. **Reading is deterministic.** The same item always hashes to the same positions and every
   estimate is an integer min — no sampling, no randomness, no run-to-run drift.

## What the demo prints

Real output of `{{ npm_name }} demo` (excerpt):

```
1. an estimate is never below the truth
  125652 updates over 300 items, 256x5 counters
  underestimates     0
  largest overestimate 211
  mean overestimate  17.13
  a collision can only add to a counter, so the estimate is an upper bound

2. the error is bounded by e/width of the updates
  width 512, depth 5
  promise            e/width * updates = 0.005309 * 125652
                     = 667.1
  largest overestimate 140
  mean overestimate  1.76
  underestimates     0

3. more width means less error
  width   promise   largest    mean
  128      2668.4       727   101.52
  256      1334.2       211    17.13
  512       667.1       140     1.76
  1024      333.6         0     0.00
  2048      166.8         0     0.00
  four times the width cut the mean overestimate by 57x on this stream
```

Story 4 proves the merge is exact (`rows identical     True`), story 5 compares the two
update styles on identical input, and story 6 checks that the five heaviest items come back
in the same order as the stream's true top five.

## Commands

```
{{ npm_name }} add --sketch seen.json --items a b a --width 1024
{{ npm_name }} estimate --sketch seen.json --item a
{{ npm_name }} info --sketch seen.json
{{ npm_name }} merge --left a.json --right b.json --out union.json
{{ npm_name }} demo
{{ npm_name }} selftest
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the command did what it says |
| 1 | reserved for a caller-side gate; the CLI never invents one |
| 2 | unusable request: missing or malformed sketch, a count below 1, mismatched shapes |

## Layout

```
src/{{ package_name }}/sketch.py    Row hashes, CountMinSketch, the bound, JSON round-trip
src/{{ package_name }}/measure.py   A deterministic skewed stream and the error report
src/{{ package_name }}/demo.py      six stories with the numbers they measure
src/{{ package_name }}/cli.py       add, estimate, info, merge, demo, selftest
src/{{ package_name }}/selftest.py  the same promises without pytest
tests/                              pytest versions of those checks
smoke.sh                            real CLI runs, including the refusal paths
```

## What this stack does not do

- No persistence beyond one JSON file, and no concurrency: the counters are plain integers.
  Merging is how two writers are combined, and it is exact for addition.
- No sliding window or decay. A sketch counts the stream since it was created; a rate needs a
  window, which is a different data structure.
- No deletion. A count-min sketch cannot subtract, because the subtraction would have to know
  which collisions it was undoing.
