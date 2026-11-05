# {{ title }}

{{ description }}

An error budget is a target plus a window: "99.9% of the calls in the last 30 days
may succeed" is 1 000 bad events per million. The budget is what is left of that
allowance, the burn rate is how fast you are spending it, and the page rule is the
two-window one from the SRE workbook — the long window decides that something is
wrong, the short window decides that it is still wrong.

## Seven numbers that get reported wrong

1. **The burn rate is a ratio of ratios.** `bad / total` divided by `allowed`. 1.0
   means exactly on pace, and it compares a 30 rps service to a 30 000 rps one.
2. **"No traffic" is not "no errors".** With zero requests the burn rate is
   undefined. This program returns nothing and says so instead of printing 0.00x,
   which is the most misleading number in the file.
3. **A missing bucket is not a good bucket.** Gaps and a window that starts before
   the first reading are printed as `missing`; counting silence as success is how
   an outage stays invisible.
4. **The budget is a rolling window.** Bad events age out, so "remaining" can go
   back up. That is a property, not a rounding error.
5. **One window alone flaps.** A single bad minute in six quiet hours is 32x burn
   over five minutes and 2.8x over six hours. Only the pair is a page.
6. **Exhaustion is not a negative remaining.** Past zero, "time to exhaustion" has
   no meaning; the report says `already exhausted` instead of "-3.2 hours".
7. **Percentages are parsed exactly.** `99.9` is 999 000 parts per million and its
   budget is 1 000, in integers and `Decimal`, never in floats.

## Use

```bash
{{ npm_name }} report --events fixtures/traffic.jsonl --window 1h
{{ npm_name }} report --events traffic.jsonl --target 99.9 --window 30d --json
{{ npm_name }} demo
{{ npm_name }} selftest
```

`report` exits 0 when nothing is over the line, 1 when a rule fires or the budget
is spent, and 2 when the input cannot be read — a misspelled target never passes.

Input is JSON Lines, one bucket per line, aligned to the width:

```json
{"at": "2026-03-08T00:00:00Z", "good": 120, "bad": 0}
```

## Layout

| path | what it holds |
| --- | --- |
| `src/{{ package_name }}/slo.py` | targets and windows, in parts per million and seconds |
| `src/{{ package_name }}/buckets.py` | reading, alignment, gaps, rolling slices |
| `src/{{ package_name }}/burn.py` | burn rate, budget, the two-window verdicts |
| `src/{{ package_name }}/demo.py` | five reports where the arithmetic is the argument |
| `src/{{ package_name }}/cli.py` | `report`, `demo`, `selftest` |

MIT licensed.
