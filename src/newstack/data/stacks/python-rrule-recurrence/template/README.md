# {{ title }}

{{ description }}

A recurrence rule is a promise about the future, and most implementations of one get the
edges wrong: they count the interval instead of the firing, they compare an instant to a
wall time, they treat the hour a zone skipped as if it happened, and they measure "the
second Tuesday" from the first of the month. This package expands a rule into instants and
explains every firing, and every skipped wall time, in terms you can check by hand.

```
$ {{ npm_name }} next --rule "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5" \
    --start 2026-01-05T09:00 --zone America/New_York --count 5
rule       FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5
start      2026-01-05 09:00:00 America/New_York
freq       WEEKLY
interval   1
byday      MO, WE, FR
wkst       MO (Monday)
bound      COUNT=5
  idx  local                 utc
  1  2026-01-05 09:00:00  2026-01-05T14:00:00Z
  2  2026-01-07 09:00:00  2026-01-07T14:00:00Z
  3  2026-01-09 09:00:00  2026-01-09T14:00:00Z
  4  2026-01-12 09:00:00  2026-01-12T14:00:00Z
  5  2026-01-14 09:00:00  2026-01-14T14:00:00Z
stopped    COUNT=5 reached
```

## Quick start

```bash
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} next --rule "FREQ=MONTHLY;BYDAY=-1FR;COUNT=3" --start 2026-01-01T17:00 --zone Europe/Berlin
PY=.venv/bin/python bash smoke.sh
```

## The six rules this package actually enforces

1. **COUNT counts firings, not intervals.** `FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5` stops
   five firings in, on the second Wednesday, not on the second Monday.
2. **UNTIL is an instant, and it is inclusive.** The comparison happens after the wall
   time has been resolved in its zone, so `09:00` in `Asia/Kolkata` is `03:30Z` and a rule
   with `UNTIL=20260303T033000Z` still fires on the third of March.
3. **A wall time the zone skipped is skipped, not guessed.** On 2026-03-08 the clocks in
   `America/New_York` jump from 02:00 to 03:00, so a daily 02:30 rule has no firing that
   day; the count is not spent on it, and the skip is reported.
4. **An hour that happens twice fires once.** The rule names a wall time, so 01:30 on
   2026-11-01 fires on its first pass, and the gap to the next firing is 25 hours.
5. **INTERVAL is counted from the start's own period.** A weekly rule steps from the week
   containing the start (whose first day is `WKST`, Monday by default), so moving the start
   by seven days moves every firing by fourteen.
6. **An ordinal weekday is counted from the edges of the month.** January 2026 starts on a
   Thursday, so `1MO` is the 5th and `-1FR` is the 30th; a month with five Fridays still
   has exactly one `-1FR`.

The seventh thing this package does is refuse impossible rules instead of looping:
`FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=30` exits 2 with `February has 29 days`, `COUNT` together
with `UNTIL` is refused as two endings for one rule, and a rule that scans its whole span
without firing says so rather than running forever.

## Commands

`next` walks forward from a start and stops at `COUNT`, `UNTIL`, `--count`, or the end of
the scan span:

```
$ {{ npm_name }} next --rule "FREQ=DAILY;COUNT=3" --start 2026-03-07T02:30 \
    --zone America/New_York --count 3
  idx  local                 utc
  1  2026-03-07 02:30:00  2026-03-07T07:30:00Z
  2  2026-03-09 02:30:00  2026-03-09T06:30:00Z
  3  2026-03-10 02:30:00  2026-03-10T06:30:00Z
skipped  2026-03-08 02:30:00  the clocks jumped forward over this wall time; the day it names never showed that hour
stopped    COUNT=3 reached
```

`between` keeps the firings whose wall time falls inside a window:

```
$ {{ npm_name }} between --rule "FREQ=MONTHLY;BYDAY=-1FR" --start 2026-01-01T17:00 \
    --since 2026-01-01T00:00 --until 2026-03-31T23:00 --zone Europe/Berlin
  1  2026-01-30 17:00:00  2026-01-30T16:00:00Z
  2  2026-02-27 17:00:00  2026-02-27T16:00:00Z
  3  2026-03-27 17:00:00  2026-03-27T16:00:00Z
firings    3
```

`explain` answers "is this one of them, and why", using the same machinery the walk uses,
so the answer cannot drift away from the expansion:

```
$ {{ npm_name }} explain --rule "FREQ=WEEKLY;BYDAY=MO" --start 2026-01-05T09:00 --at 2026-01-07T09:00
at         2026-01-07 09:00:00
verdict    not an occurrence
reason     Wednesday on day 7 matches none of BYDAY=MO
```

`demo` runs six worked stories; `selftest` re-checks sixty known answers; both exit non-zero
if anything stops holding.

## Input

- `--rule` is RRULE text, with or without the `RRULE:` prefix. Keys: `FREQ` (DAILY, WEEKLY,
  MONTHLY, YEARLY), `INTERVAL`, `COUNT`, `UNTIL`, `BYDAY`, `BYMONTHDAY`, `BYMONTH`, `WKST`.
  Unknown keys are refused, not ignored.
- `--start` is a **wall time** (`2026-01-05T09:00`), never an instant: a rule repeats a wall
  time, and `--zone` decides which instant that is. A start with an offset is refused.
- `UNTIL` is an **instant** (`20260303T033000Z` or an ISO time with an offset), and it is
  inclusive.

## Exit codes

| code | meaning |
|------|---------|
| 0 | the command answered |
| 1 | there is no occurrence to answer with (an empty window, a rule that never fires, a date that is not a firing) |
| 2 | the question was unusable: a bad rule, an unknown zone, an offset start, an inverted window |

## Layout

```
src/{{ package_name }}/
  rrule.py     parse the rule, refuse the impossible ones at parse time
  expand.py    walk periods, filter days, resolve wall times in a zone
  explain.py   answer "is this a firing" with the same machinery
  demo.py      six stories, each with claims checked while it prints
  cli.py       next / between / explain / demo / selftest
  selftest.py  the same known answers, without pytest
tests/         the rule, the walk, the explanations, and the command line
fixtures/      five rules covering the interesting edges
```

## What this package does not do

- It does not implement the whole RFC 5545: no `BYSETPOS`, `BYHOUR`, `BYWEEKNO`, `RDATE` or
  `EXDATE`. The keys it accepts are the ones it can defend.
- It does not decide what to do when a firing is ambiguous in the *policy* sense — it takes
  the first pass of a repeated wall time, and says so.
- It does not schedule anything. It tells you what the rule means.
