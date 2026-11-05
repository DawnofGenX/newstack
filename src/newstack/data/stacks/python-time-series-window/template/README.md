# {{ title }}

{{ description }}

A windowed aggregate looks trivial until you ask when it was true. Every number
this program prints carries the moment it became final, and every event that
arrived after that moment is reported instead of folded in.

## Seven lies a windowing job tells

1. **"The window starts at the first event."** Align to the epoch instead
   (`floor(t / width) * width`). Alignment to the data makes the same input
   produce different windows depending on which event happened to arrive first.
2. **"Late data is dropped."** It is dropped only because the design cannot say
   otherwise. Here an event late but inside the allowed lateness changes the
   aggregate, because that aggregate does not exist yet.
3. **"Late data was counted."** An event that arrives after its window was
   emitted is `too_late`, and the number it would have changed stays exactly
   where it was. Rewriting yesterday's report is worse than admitting a late row.
4. **"The watermark is the wall clock."** It is `max(event time seen) - lateness`.
   Derived from data, a replay of the same file gives the same report; derived
   from `now`, it never can.
5. **"A missing window is a zero."** A window with no events has no count. It is
   listed under `missing`, because 0 is a measurement and silence is not.
6. **"The mean of nothing is 0.0."** When every event in a window carries a null
   value, the mean is undefined and prints as `-`. `sum` behaves the same way.
7. **"The last window is final."** At end of input the buffer is flushed with
   `final: false`: no watermark reached it, so more data could still arrive.

## Use

```bash
{{ npm_name }} run --events fixtures/traffic.jsonl --width 60s
{{ npm_name }} run --events fixtures/late.jsonl --width 60s --lateness 30s
{{ npm_name }} run --events traffic.jsonl --width 5m --hop 1m --agg sum --json out.json
{{ npm_name }} demo
{{ npm_name }} selftest
```

`run` exits 0 when every event was counted, 1 when at least one arrived too late
to count (a data-quality gate, not a footnote), and 2 when the input cannot be
read. `--width`, `--hop` and `--lateness` accept `500ms`, `30s`, `5m`, `1h` or a
bare number of seconds.

Input is JSON Lines, one event per line, in arrival order:

```json
{"t": "2026-01-01T00:00:10+00:00", "value": 12.5}
```

`value` may be `null`. `t` must carry a UTC offset: a naive timestamp is a local
guess, and guessing is how two machines disagree about yesterday.

## Layout

| path | what it holds |
| --- | --- |
| `src/{{ package_name }}/events.py` | timestamps, values, the JSONL reader |
| `src/{{ package_name }}/windows.py` | half-open windows, epoch alignment, tiling and sliding |
| `src/{{ package_name }}/engine.py` | the watermark, the buffer, the aggregates, the late list |
| `src/{{ package_name }}/demo.py` | six stories where the timing is the argument |
| `src/{{ package_name }}/cli.py` | `run`, `demo`, `selftest`, exit codes |

## Layout of a report

```
aggregation count  width 60s  hop -  lateness 0s
watermark   2026-01-01T00:07:40Z

window                                  count       total          mean  final
2026-01-01T00:00:00Z..2026-01-01T00:01:00Z      3       33.6          11.2  yes
2026-01-01T00:03:00Z..2026-01-01T00:04:00Z      3       43.8          14.6  yes
```

`final: yes` means the watermark closed the window. `final: no` means the input
ended first, so the number is a lower bound on a window that is still open.

MIT licensed.
