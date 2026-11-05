# {{ title }}

A five-field cron expression parsed into the set of values it means, then answered
as what actually runs: a list of UTC instants, each with the wall clock it
corresponds to in a named zone.

The expression language is the easy half. The hard half is that a schedule is
written against a *local* clock and a job fires at an *instant*, and twice a year
those two disagree. This tool makes both disagreements visible instead of
surprising:

* a local time that DST skips has **no run** that day (2026-03-08 02:30 does not
  exist in New York);
* a local time that DST repeats runs **twice** (2026-11-01 01:30 happens in EDT
  and again in EST).

No dependencies outside the standard library; the zone database comes from the
system (`zoneinfo`).

## Quick start

```
uv venv
uv pip install -e . pytest ruff

$ {{ npm_name }} next "30 2 * * *" --after 2026-03-07T12:00:00Z \
      --tz America/New_York --count 3
after    2026-03-07T12:00:00Z
zone     America/New_York
 1  2026-03-09T06:30:00Z  = 2026-03-09 02:30 EDT  America/New_York
 2  2026-03-10T06:30:00Z  = 2026-03-10 02:30 EDT  America/New_York
 3  2026-03-11T06:30:00Z  = 2026-03-11 02:30 EDT  America/New_York

$ {{ npm_name }} explain "0 0 1 * 1"
expression 0 0 1 * 1
minute     0
hour       0
day        1
month      every
weekday    1
day rule   or   both fields are restricted, so either one matches (Vixie cron)

$ {{ npm_name }} next "*/0 * * * *"
{{ npm_name }}: field minute: a step must be at least 1, got 0
$ echo $?
2

$ PY=.venv/bin/python bash smoke.sh
29 passed, 0 failed
smoke: all checks passed
```

## Commands

```
next EXPRESSION [--count N] [--after MOMENT] [--tz ZONE] [--json]
explain EXPRESSION        what each field means, and how the day fields were joined
demo                      six schedules, computed
selftest                  the same claims, without the prose
```

`--after` must carry an offset (`2026-03-07T12:00:00Z` or `+05:30`); a naive
timestamp is refused, because "noon" is the thing this tool is trying to stop you
from being vague about. `--tz` defaults to `UTC`. Exit codes: `0` fine, `1` the
expression is valid but has no run in the next eight years, `2` unusable input.

## The two DST cases

New York springs forward on 2026-03-08: at 07:00 UTC the local clock jumps from
02:00 to 03:00. Every minute of 02:00–02:59 is missing, so `30 2 * * *` has
nothing to match that day:

```
the run before   2026-03-07 02:30 EST  (07:30 UTC)
next run         2026-03-09 02:30 EDT  (06:30 UTC)
the gap between them is 47 hours
```

New York falls back on 2026-11-01: 01:00–01:59 happens in EDT and then again in
EST, so `30 1 * * *` matches twice, an hour apart on the clock and the same
minute on the wall:

```
 1  2026-11-01T05:30:00Z  = 2026-11-01 01:30 EDT  America/New_York
 2  2026-11-01T06:30:00Z  = 2026-11-01 01:30 EST  America/New_York
 3  2026-11-02T06:30:00Z  = 2026-11-02 01:30 EST  America/New_York
```

This is not an accident of the implementation. The runs are found by walking UTC
minutes and converting each candidate into the zone, so "does this local time
exist" is answered by the zone database rather than by a guess. A schedule that
is written in UTC can never hit either case, which is the reason
`--tz UTC` is the default.

## The demo, verbatim

```
every fifteen minutes              as advertised
  next     12:15 UTC
  next     12:30 UTC
  next     12:45 UTC

day 1 or Monday, not both          as advertised
  2026-03-09 Mon  00:00 UTC
  2026-03-16 Mon  00:00 UTC
  2026-03-23 Mon  00:00 UTC
  2026-03-30 Mon  00:00 UTC
  2026-04-01 Wed  00:00 UTC

the hour that never happens        as advertised
  the run before   2026-03-07 02:30 EST  (07:30 UTC)
  next run         2026-03-09 02:30 EDT  (06:30 UTC)
  2026-03-08 02:30 does not exist in New York, so that day has no run
  the gap between them is 47 hours

the hour that happens twice        as advertised
  2026-11-01T05:30:00Z  2026-11-01 01:30 EDT
  2026-11-01T06:30:00Z  2026-11-01 01:30 EST
  2026-11-02T06:30:00Z  2026-11-02 01:30 EST
  01:30 happens twice on 2026-11-01, so the job runs twice

a step of zero                     as advertised
  refused   field minute: a step must be at least 1, got 0

Sunday is 0 and 7                  as advertised
  weekday 7 -> values [0]
  weekday 0 -> values [0]
  the same schedule, and the next run is 2026-03-08 Sun

demo: 6 schedules, 0 not as advertised
```

## Seven traps this gets right

1. **Day-of-month and day-of-week are joined with OR, not AND.** `0 0 1 * 1`
   fires on the 1st *and* on every Monday — the Vixie cron rule, and the reason
   that expression is not "Mondays that fall on the 1st". When only one of the
   two is restricted, the starred field cannot veto it, so the join is AND.
2. **Sunday is both 0 and 7.** Both spell the same day, `mon-fri` is a name for
   `1-5`, and `jan` is `1`.
3. **A step is a stride over a range.** `*/15` is four values in an hour,
   `10-20/5` is three of them, and `*/0` is refused rather than treated as "every
   minute".
4. **A missing hour is not a skipped job to be papered over.** The run genuinely
   does not happen; the gap between runs is 47 hours, and a checker that silently
   *shifts* it to 03:30 is telling you a story about a job that never ran.
5. **A repeated hour runs twice.** The second run is one hour later in UTC and
   identical on the wall clock; the two offsets in the output are the evidence.
6. **A naive moment is refused.** `--after 2026-03-07T12:00:00` is an error, not
   a guess at UTC: the entire subject is which zone a wall clock belongs to.
7. **"Valid" and "fires" are different answers.** `0 0 30 2 *` parses cleanly and
   describes nothing — February never has 30 days — so it exits `1` with the
   window it searched, instead of printing an empty list as if that were success.

## What this is not

Not a scheduler: it does not run jobs, hold leases, retry, or persist state. It
also does not model the `@reboot`, `@daily` or second-field extensions some cron
dialects accept — five fields, checked, or a refusal. Where a daemon and this
tool would disagree about a DST night, the daemon is the one that decides; this
tool is for knowing, in advance, which instants you are asking it to decide
about.

## Layout

| path | what it holds |
| --- | --- |
| `src/{{ package_name }}/model.py` | fields, `Schedule`, `runs_after` (the UTC walk and the day skip) |
| `src/{{ package_name }}/cli.py` | `next`, `explain`, `demo`, `selftest` |
| `src/{{ package_name }}/demo.py` | the six schedules above |
| `tests/test_dst.py` | the two DST cases, in New York and London |
