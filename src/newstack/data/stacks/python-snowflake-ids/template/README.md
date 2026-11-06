# {{ title }}

{{ description }}

An identifier is three fields: 41 bits of milliseconds, 10 bits of worker, and
12 bits of sequence. Those sizes are not decoration. They decide how many
workers exist, how many identifiers one worker may issue in a millisecond, and
how long the layout lasts. This stack writes the sizes down, checks every value
that must fit them, and shows what the clock does to the sequence.

## The rules this generator keeps

1. **The number is the fields.** `compose` refuses anything that does not fit
   its bits, and `decode` refuses anything that is not one of ours, so an
   identifier never silently carries a truncated worker.
2. **The sequence is a promise the clock cannot keep.** 12 bits allow 4096
   identifiers in one millisecond; the 4097th waits for the next millisecond
   and the wait is counted, not hidden.
3. **A backwards clock is refused, not smoothed over.** The default strategy
   raises after naming how far the clock moved back. `--on-rollback hold`
   keeps issuing inside the last millisecond it saw and spends the sequence
   budget; when that budget is gone and the clock cannot move, it raises.
4. **Two workers cannot collide.** The worker field is part of the number, so
   the same millisecond and the same sequence still produce different
   identifiers, and every worker has its own number space.
5. **Order is field order.** Sorting identifiers by their integer value sorts
   by millisecond, then worker, then sequence: the arrival order of two workers
   is not the identifier order, and the worker field is the tiebreak.
6. **The layout is a budget.** 4096 identifiers per millisecond is 4,096,000
   per second per worker, 1024 workers is the ceiling, and 41 bits of
   milliseconds end in 2093 for this epoch.

## See it

```
$ {{ npm_name }} demo
1. an identifier is a timestamp you can read back
  4194332672  at 2024-01-01T00:00:01+00:00  worker 7  sequence 0
  4198526976  at 2024-01-01T00:00:01.001000+00:00  worker 7  sequence 0
  4202721280  at 2024-01-01T00:00:01.002000+00:00  worker 7  sequence 0
  the worker field survives the round trip: yes
  each millisecond restarts the sequence: yes
  the time field counts milliseconds: yes
  -> holds

2. the sequence fills one millisecond, then the clock must move
  identifiers   5000
  in ms 0       4096 (the whole sequence is 4096)
  in ms 1       904
  waits         1
  one millisecond holds exactly the sequence: yes
  the overflow waited for the next millisecond: yes
  the sequence restarts after the wait: yes
  -> holds

3. a clock that runs backwards: refuse or hold
  refuse        the clock moved back 10 ms after identifier 1; issuing again would reuse a millisecond, so this generator refuses
  the default generator refuses a backwards step: yes
  hold          sequences [1, 2, 3] at ms 1000
  holding keeps issuing inside the last millisecond: yes
  the holds are counted: yes
  exhausted     after 4095: 4096 identifiers in one millisecond is the whole sequence, and this clock cannot move forward to the next one
  the held sequence is a finite budget: yes
  -> holds

4. two workers in one millisecond cannot collide
  worker 0      4194304000
  worker 1      4194308096
  the same millisecond and sequence still differ: yes
  capacity      1024 workers x 4096 = 4,194,304 per ms
  every worker has its own number space: yes
  the last worker is still readable: yes
  -> holds

5. the layout is a budget, and it runs out
  time         41 bits = 2199023255551 ms = 69.68 years
  worker       10 bits = 1024 workers
  sequence     12 bits = 4096 identifiers per worker per ms
  throughput   4,096,000 per second per worker
  layout ends  2093-09-06T15:47:35.551000+00:00
  ...
  -> holds

stories      6 of 6 hold
```

## Issue some identifiers

```
$ {{ npm_name }} generate --count 3 --worker 4 --spread
16384  2024-01-01T00:00:00+00:00  worker 4  sequence 0
4210688  2024-01-01T00:00:00.001000+00:00  worker 4  sequence 0
8404992  2024-01-01T00:00:00.002000+00:00  worker 4  sequence 0
issued       3 identifier(s) from worker 4
waits        0
```

`--spread` advances the clock by one millisecond per identifier, so the
sequence stays at zero. Without it the run fills the sequence in a single
millisecond, which is what `--count 4100` shows:

```
$ {{ npm_name }} generate --count 4100 --worker 1
...
issued       4100 identifier(s) from worker 1
waits        1
```

## Read one back

```
$ {{ npm_name }} decode 20975718400
20975718400  at 2024-01-01T00:00:05.001000+00:00  worker 1  sequence 0
```

## Audit a stream

```
$ {{ npm_name }} audit --input fixtures/ids.jsonl
identifiers  12
distinct     12 (0 duplicate(s))
order        strictly increasing
workers      1
span         11 ms
rate         1,091 identifier(s) per second
verdict      sound
```

`audit` exits 0 only when the stream has no duplicates and never steps back;
a duplicate or a step back exits 1, and unusable input (missing file, an empty
file, a value that is not a number) exits 2.

## The capacity of the layout

```
$ {{ npm_name }} capacity
time         41 bits = 2199023255551 ms = 69.68 years
worker       10 bits = 1024 workers
sequence     12 bits = 4096 identifiers per worker per ms
throughput   4,096,000 per second per worker
layout ends  2093-09-06T15:47:35.551000+00:00
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the run finished; a stream was audited and found sound |
| 1 | the audited stream has a duplicate or a step back |
| 2 | unusable input: missing or empty file, a worker or value outside the layout |

## Layout

| path | what it holds |
| ---- | ------------- |
| `src/{{ package_name }}/layout.py` | the 64 bits, `compose`, `decode`, the capacity numbers |
| `src/{{ package_name }}/generator.py` | the clock, the sequence, and the two rollback strategies |
| `src/{{ package_name }}/audit.py` | order, duplicates, workers, rate, spacing |
| `src/{{ package_name }}/demo.py` | the six stories above |
| `src/{{ package_name }}/cli.py` | `generate`, `decode`, `audit`, `capacity`, `demo`, `selftest` |

## What this stack does not do

- It does not synchronise clocks. Every worker needs a clock that moves
  forward, and the generator's job is to notice when it does not.
- It does not retry or sleep in a loop for a backwards clock: that decision
  belongs to the caller, who knows whether the work can wait.
- It does not encode a datacentre or a shard beyond the 10 worker bits; a
  different split is a different layout, and `compose` will not guess.

## Quick start

```
cd your-project
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
.venv/bin/python -m pytest -q
PY=.venv/bin/python bash smoke.sh
```
