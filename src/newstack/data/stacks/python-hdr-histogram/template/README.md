# {{ title }}

{{ description }}

A percentile from a bucket can only be as precise as the bucket. This stack
stores latencies in a fixed layout of counters, prints the promised relative
error beside every answer, and checks each answer against the true
nearest-rank value computed from the raw samples.

## The rules this histogram keeps

1. **A bucket is a range, and the reported value is its ceiling.** Reading a
   bucket cannot invent precision the counter does not have, so every
   percentile is the upper edge of its bucket: never below the truth.
2. **The layout is the promise.** At 10 significant bits the relative width of
   a bucket is at most `1/1024` = 0.0977%. That number is printed, not implied,
   and every reported percentile is checked against it.
3. **The count, the sum, and the minimum are exact.** Bucketing approximates
   values, never counts. A sample cannot be dropped, so `count` and `total_sum`
   are the same numbers a raw list would give.
4. **A merge of two histograms equals one pass over both samples.** Buckets add
   pointwise and only for the same layout; two different resolutions are
   refused, because their bucket boundaries do not line up.
5. **Memory follows the value range, not the sample count.** The footprint is
   the counters up to the highest bucket a value landed in, so a million
   samples and a thousand samples over the same range cost the same.
6. **Percentiles do not average.** The p95 of a merge is not the mean of the
   two p95s; the average is printed next to the pooled value and the truth.
7. **Resolution is a decision you pay for.** Fewer bits means wider buckets,
   a wider gap, and fewer bytes; the demo prints the whole trade.

## See it

```
$ {{ npm_name }} demo
1. a percentile from a bucket can only be as precise as the bucket
  samples      200000, significant bits 10
  buckets      5611 used of a layout sized for the value range
  p50    reported      11983 truth      11977 gap   0.0501%
  p90    reported      25935 truth      25935 gap   0.0000%
  p99    reported      48703 truth      48699 gap   0.0082%
  p99.9  reported      77055 truth      77014 gap   0.0532%
  worst gap 0.0532% against a promised 0.0977%: held
  every reported percentile within the promise: yes
  the reported value is never below the truth: yes
  -> holds
...
4. memory follows the value range, not the sample count
  1,000 samples    60408 byte(s), 861 bucket(s) used
  200,000 samples  73368 byte(s), 5584 bucket(s) used
  200x the samples cost less than 2x the bytes: yes
  per sample       1,000: 60.41 B, 200,000: 0.3668 B
  the per-sample cost falls by more than an order of magnitude: yes
  the counters are sized by the values the samples touch; the count only fills them
  -> holds
...
5. the average of two percentiles is not the percentile
  endpoint A p95 14215 us, endpoint B p95 160127 us
  average of the two p95s 87171 us
  p95 of everything       123519 us
  p95 of the raw samples  123457 us
  the pooled p95 matches the raw samples: yes
  the averaged p95 is far from the truth: yes
  -> holds

stories      6 of 6 hold
```

## Check the promise on your own numbers

```
$ {{ npm_name }} percentile --input fixtures/latencies.jsonl --p 50,95,99
left         240 sample(s), promised 0.0977%
  p50    reported      12511 truth      12506 gap   0.0400%
  p95    reported      81343 truth      81325 gap   0.0221%
  p99    reported     167935 truth     167880 gap   0.0328%
  worst gap 0.0400% against a promised 0.0977%: held
result       within the promise
```

The `truth` column is the nearest-rank percentile of the raw samples, using the
same one-based rule the histogram uses, so the comparison is not a comparison of
two definitions. `--json` prints the same numbers as a document; the process
exits 1 if any gap exceeds the promise.

## Keep a histogram and merge it later

```
$ {{ npm_name }} record --input fixtures/latencies.jsonl --out histogram.json
samples      240
bits         10 (relative error at most 0.0977%)
buckets      233 used, 80504 byte(s)
written      histogram.json

$ {{ npm_name }} info --histogram histogram.json
samples      240
minimum      2465
mean         24489.3
p99          167935
buckets      233 used, 80504 byte(s)
bits         10 (relative error at most 0.0977%)
```

`record` writes one JSON document; `merge --left a.json --right b.json` adds two
of them and refuses a pair with different resolutions; `info` reads one back.

## Input

`--input` accepts JSON Lines where a line is either a bare whole number or an
object with a `latency` field:

```
1205
{"latency": 812}
```

Floats, negative values, and anything past the configured layout are refused
with the line number, because a silently rounded latency is a percentile you
cannot defend.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the run finished and every percentile is inside the promised error |
| 1 | a percentile is outside the promise (the comparison still printed) |
| 2 | unusable input: missing file, no samples, unreadable percentile, foreign document |

## Layout

| path | what it holds |
| ---- | ------------- |
| `src/{{ package_name }}/histogram.py` | the layout, `record`, percentiles, the merge |
| `src/{{ package_name }}/stats.py` | the truth side: nearest rank, the gap check, the average trap |
| `src/{{ package_name }}/demo.py` | the six stories above |
| `src/{{ package_name }}/cli.py` | `percentile`, `record`, `merge`, `info`, `demo`, `selftest` |
| `tests/` | the layout, the promise, and the command line |

## What this stack does not do

- It does not track a time window: a histogram is a snapshot, so rotate it and
  merge the snapshots yourself.
- It does not compensate for coordinated omission, so a latency must be
  measured from the moment the request became due.
- It does not promise exact percentiles. It promises a bound, prints it, and
  checks every answer against the truth.

## Quick start

```
cd your-project
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
.venv/bin/python -m pytest -q
PY=.venv/bin/python bash smoke.sh
```
