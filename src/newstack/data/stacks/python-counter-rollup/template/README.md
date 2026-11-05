# {{ title }}

{{ description }}

A counter reading is a level. `requests_total 40213` says nothing on its own — it is
not a rate, and it is not a traffic number. Turning readings into a number you can
put on a dashboard means answering, in the code and in writing:

- which time window does an increase belong to, and what if it straddles a boundary?
- what does a counter restart look like, and why is it not a negative delta?
- what does a missing scrape mean — zero traffic, or nothing observed?
- what happens when the same rollup is delivered twice by an at-least-once transport?

This project answers all four, prints the arithmetic it used, and has a `demo`
that fails if any answer stops being true.

## Quick start

```console
$ uv venv --allow-existing .venv
$ uv pip install -e . pytest ruff
$ python -m {{ package_name }} demo
$ python -m {{ package_name }} rollup --file readings.jsonl --width 10 --name requests
```

## A steady counter

`readings.jsonl` holds one JSON object per line, microseconds since the epoch and the
counter's value at that instant:

```json
{"at_us": 0, "value": 0}
{"at_us": 10000000, "value": 100}
{"at_us": 20000000, "value": 200}
{"at_us": 30000000, "value": 300}
```

```console
$ python -m {{ package_name }} rollup --file readings.jsonl --width 10 --name requests
name         shard          window    total   n rst       rate
requests     default      10000000      100   1  0   10.000/s
requests     default      20000000      100   1  0   10.000/s
requests     default      30000000      100   1  0   10.000/s
windows  3 with readings, 0 without; 30.000s observed
rate     10.000/s over the windows that were actually measured
```

Three windows, not four: the reading at `0` is the *start* of the first interval, and
an interval is what carries an increase. The timeline touches four windows; only three
of them were measured.

## A scrape that never happened

```console
$ python -m {{ package_name }} rollup --file holed.jsonl --width 10 --name requests
name         shard          window    total   n rst       rate
requests     default      10000000       10   1  0    1.000/s
requests     default      20000000       10   1  0    1.000/s
requests     default      40000000       20   1  0    1.000/s
requests     default      50000000       10   1  0    1.000/s
windows  4 with readings, 1 without; 50.000s observed
rate     1.000/s over the windows that were actually measured
gap      window 30000000..40000000 has no reading; that window is unknown, not zero
$ echo $?
1
```

The gap exits `1`: a rate whose middle window is missing is not the rate, and the
command says so instead of printing a zero. Note the sources of that `20` — the
increase between the readings at 20 s and 40 s is one measurement, and it belongs to
the window containing the *later* reading. Splitting it into `10 + 10` would be
inventing two numbers nobody measured. `covered_us` in the JSON records how much time
each window actually observed, so the rate is checkable from the artifact itself.

## A counter that restarts

```console
$ python -m {{ package_name }} rollup --file reset.jsonl --width 10 --shard a --json
{
  "width_us": 10000000,
  "rollups": [
    {
      "name": "requests",
      "shard": "a",
      "window": {"start_us": 10000000, "end_us": 20000000},
      "total": 100, "samples": 1, "resets": 0,
      "first_us": 0, "last_us": 10000000, "covered_us": 10000000
    },
    {
      "name": "requests",
      "shard": "a",
      "window": {"start_us": 20000000, "end_us": 30000000},
      "total": 20, "samples": 1, "resets": 1,
      "first_us": 10000000, "last_us": 20000000, "covered_us": 10000000
    }
  ],
  "gaps": [],
  "rate_per_second": 10.0
}
```

The counter read `600` and then `20`. The increase is `20`, not `-580`: the process
restarted, the old counter died at an unknown instant, and the new counter has counted
20 events since. `resets: 1` is the flag that tells you why that window looks odd —
which is exactly the thing dashboards get wrong, silently.

## Merging what the network delivered twice

```console
$ python -m {{ package_name }} merge a.json b.json
merged   2 window(s), 2 repeat(s) dropped
name         shard          window    total   n rst       rate
requests     a            10000000      100   1  0   10.000/s
requests     a            20000000       20   1  1    2.000/s
combined across shards
name         shard          window    total   n rst       rate
requests     *            10000000      100   1  0   10.000/s
requests     *            20000000       20   1  1    2.000/s
```

`a.json` and `b.json` are the same file, delivered twice. The merged total is the
traffic, not twice the traffic. A repeat that *disagrees* is refused instead of being
averaged, because two different numbers for one window mean the producer has a bug:

```console
$ python -m {{ package_name }} merge a.json conflict.json
{{ npm_name }}: shard a reports 100 and 101 for the window starting 10000000; one of them is wrong, and adding them would be worse
```

`combine` is the other operation: shards partition the traffic, so their totals add,
and coverage becomes the union of what each shard observed.

## Exit codes

| code | meaning |
| ---- | ------- |
| `0` | every window was measured, or the merge was clean |
| `1` | at least one window has no reading (`rollup`), or a demo scenario broke |
| `2` | the input is unusable: unreadable file, no readings, conflicting repeats |

## The traps this stack encodes

1. **A counter is a level, not a rate.** One reading has no duration, so it produces
   no window at all rather than a zero.
2. **Windows are floor-aligned, never rounded.** Rounding moves a boundary, and two
   scrapers that disagree about a boundary produce two different answers for the same
   event.
3. **An increase belongs to the window of the later reading.** An interval that
   straddles a boundary is one measurement; splitting it would invent two. The cost is
   that `covered_us` can start before `window.start_us`, which is why it is reported.
4. **A restart is not a negative delta.** The new value *is* the increase, and `resets`
   counts how often it happened.
5. **A missing window is absent, not zero.** Nobody scraped, so nothing is known about
   that window. `rollup` exits `1` and names it.
6. **At-least-once delivery means duplicates.** An exact repeat is dropped; a repeat
   that disagrees raises `Conflict`. Adding both would multiply the traffic by the
   retry count.
7. **`samples` counts intervals, not readings.** A window with one interval over ten
   seconds has a rate; a window with one reading does not exist.
8. **Time is integer microseconds.** Floats drift and `datetime` arithmetic in local
   time wanders across a DST change; the width you type in seconds is converted once,
   at the edge.

## Layout

| path | what lives there |
| ---- | ---------------- |
| `src/{{ package_name }}/model.py` | `Sample`, `Window`, `Rollup`, `delta_for`, alignment |
| `src/{{ package_name }}/rollup.py` | folding readings into windows, gap detection |
| `src/{{ package_name }}/merge.py` | duplicate-safe merge, cross-shard combine, JSON round trip |
| `src/{{ package_name }}/demo.py` | four scenarios, each asserting its own claim |
| `src/{{ package_name }}/cli.py` | `rollup`, `merge`, `demo`, `selftest` |

## What this is not

It is not a metrics database: there is no storage, no query language and no query
across labels. It is the arithmetic between a scrape and a dashboard, written down so
it can be reviewed — put a real TSDB behind it when you need retention.
