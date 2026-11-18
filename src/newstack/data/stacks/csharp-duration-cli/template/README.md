# {{ title }}

{{ description }}

Durations written in ISO 8601 look simple until you have to add one to a
timestamp: `P1M` means a month, and a month is 28 to 31 days. This tool holds a
duration as a `TimeSpan`, parses the unambiguous forms — weeks, days, hours,
minutes, seconds — and refuses calendar units instead of guessing.

## Layout

```
IsoDuration.cs        ParseIso / ParseHuman / ToIso / ToHuman / AddTo
Program.cs            Durations.Run(): parse | add | between, plus the usage text
tests/                xunit: parse tables, round trips, month-boundary addition, CLI exit codes
```

## Usage

```console
$ dotnet build
$ ./bin/Debug/net8.0/{{ npm_name }} parse 1h30m
seconds=5400
iso=PT1H30M
human=1h30m
$ ./bin/Debug/net8.0/{{ npm_name }} add P1D --from 2026-01-31T23:30:00Z
from=2026-01-31T23:30:00Z
to=2026-02-01T23:30:00Z
$ ./bin/Debug/net8.0/{{ npm_name }} between 2026-01-01T00:00:00Z 2026-01-02T01:00:00Z
seconds=90000
iso=P1DT1H
human=1d1h
```

Either spelling is accepted everywhere: `P2DT3H4M5S` and `2d3h4m5s` are the same
value, and a leading `-` (or `-P...`) makes a duration negative.

## What is refused, and why

| input | reason |
| ----- | ------ |
| `P1Y`, `P3M` | calendar years and months are ambiguous; express them as weeks or days |
| `PT` / `P` | no components |
| `1h30` | an amount without a unit |
| `next tuesday` | not a duration |

`M` before the `T` is months; `M` after it is minutes — the parser looks only at
the date part for calendar units, so `PT3M` is three minutes.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` |
| 1 | a duration or timestamp could not be parsed |
| 2 | usage error (unknown command, missing or extra arguments, bad `--from`) |

## Test

```console
$ dotnet test
$ bash smoke.sh
```
