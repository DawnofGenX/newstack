# {{ title }}

{{ description }}

`{{ npm_name }}` builds a filter from a budget instead of a guess, then measures what it actually
does. The one guarantee a Bloom filter has — **no false negatives** — is checked against every
item that was added. The false-positive rate is measured against the formula at three budgets.
Removal is shown breaking the guarantee, and the counting filter is shown fixing it.

## The rules this filter keeps

1. **Size from the budget, not from habit.** `m = ceil(-n ln p / (ln 2)^2)` bits and
   `k = round(m/n ln 2)` hashes. A 1% target at 1000 items is 9586 bits and 7 hashes: 9.59 bits
   per item. The formula is printed with the answer, so the arithmetic can be checked.
2. **One digest, k positions.** `h_i = h1 + i·h2 (mod m)`, both halves of a 16-byte BLAKE2b
   digest — Kirsch–Mitzenmacher. Two hash functions' worth of entropy give the k positions, and
   `h2` is forced odd so the walk cannot collapse onto one position.
3. **A yes is a maybe; a no is a no.** Every item that was added must answer yes, forever. That
   is the only promise, and the whole suite is built around not breaking it.
4. **The rate is a rate.** A 1% filter does not answer no to 99% of absent items in one run; it
   answers yes to about 1% of them. `measure.false_positive_rate` probes absent items and reports
   the fraction, and the demo compares it with `(1 - e^(-kn/m))^k`.
5. **More hashes is not better.** The k that minimises the rate is a function of m/n. The demo
   sweeps k from 1 to 12 on a fixed bit array: the measured rate bottoms out at the textbook
   value and climbs on both sides.
6. **Removal is a lie unless it is counted.** Clearing an item's bits also clears the bits that
   other items rely on, so the filter starts answering *no* to something it was told — a false
   negative, which a Bloom filter is not allowed to have. `CountingBloom` keeps one saturating
   byte counter per position and only decrements, which cannot erase another item's evidence.
7. **Saturation is reported.** At fill 1.0 the filter answers yes to everything while still
   looking like a filter. `info` prints fill, the estimated item count and the predicted rate, and
   exits non-zero once the fill passes 0.9.

## Quickstart

```console
$ uv venv --allow-existing .venv
$ uv pip install --python .venv/bin/python -e . pytest ruff
$ .venv/bin/python -m {{ package_name }} sized --expected 1000 --rate 0.01
expected    1000 item(s)
target rate 0.010000
bits        9586 (9.59 per item)
hashes      7
predicted   0.010035 at full capacity
```

```console
$ .venv/bin/python -m {{ package_name }} create --filter items.json --expected 1000
created     items.json
bits        9586
hashes      7
kind        bloom
$ .venv/bin/python -m {{ package_name }} add --filter items.json --item alpha --item beta
added       alpha                    new bits 7 of 7
added       beta                     new bits 7 of 7
fill        0.0015 of 9586 bits
$ .venv/bin/python -m {{ package_name }} check --filter items.json --item gamma
absent      gamma (definite: nothing that was added shares its bits)
$ echo $?
1
```

`check` exits `0` for present and `1` for absent, so a shell `if` can use it. A present answer
still prints *maybe*, because a false positive is the price of the memory.

## What the demo measures

```text
2. the false-positive rate is a number you can check
  the formula promised a rate; 20000 absent items were then probed
    target     bits   k  predicted   measured
    0.0070    20655   7     0.0070     0.0069
    0.0100    19171   7     0.0100     0.0095
    0.0125    18242   6     0.0125     0.0128

3. past the optimum, more hashes make it worse
  19171 bits fixed, 2000 items, sweep the hash count
  k   predicted  measured
   1     0.0991    0.1125
   4     0.0135    0.0143
   7     0.0100    0.0103 <- best
  10     0.0130    0.0145
  12     0.0176    0.0195

4. removal is where the guarantee dies, and counters are the way back
  candidate-0 and candidate-1 share at least one position
  after clearing the bits of candidate-1:
    plain filter     candidate-0 present = False
    counting filter  candidate-0 present = True
```

## Sizing table

| items | target rate | bits | hashes | bits per item |
| --- | --- | --- | --- | --- |
| 1,000 | 10% | 4,793 | 3 | 4.79 |
| 1,000 | 1% | 9,586 | 7 | 9.59 |
| 1,000 | 0.1% | 14,378 | 10 | 14.38 |
| 1,000,000 | 1% | 9,585,059 | 7 | 9.59 |

Bits per item depends on the rate alone; the hashes are the rounded optimum for that ratio.

## Commands

| command | what it does |
| --- | --- |
| `sized --expected N --rate P` | print the bits, hashes and predicted rate for a budget |
| `create --filter F --expected N [--rate P] [--kind bloom\|counting]` | write an empty filter |
| `add --filter F --item X [--item Y ...]` | set (or increment) an item's positions |
| `check --filter F --item X` | exit 0 present, 1 absent |
| `info --filter F` | fill, estimate, predicted rate and verdict |
| `demo` | the five measurements |
| `selftest` | 67 checks over the whole module |

| exit code | meaning |
| --- | --- |
| `0` | the command did what was asked (for `check`: it is *maybe* present) |
| `1` | `check` says absent, or `info` says the filter is saturated |
| `2` | the arguments, the file or the parameters cannot be used as given |

## What this stack does not do

No deletion from a plain filter — that is what the counting filter is for. No unbounded counters:
255 is the ceiling, so a position shared by more than 255 adds saturates and stops decrementing
accurately. No capacity stored in the file, so `info` can only report the fill and the estimate.
No proof of hash independence: k positions come from two hash values, which is the standard
approximation and the reason the measured rate sits close to, but not exactly at, the formula.
