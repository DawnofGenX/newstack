# {{ title }}

{{ description }}

Cron tells you when something *would* run; this tells you when it *will*. Give
it a five field expression and it prints the next firing times in UTC, or
explains what each field means.

## Usage

```sh
./bin/{{ package_name }} -n 3 '*/15 * * * *'
./bin/{{ package_name }} --from 2024-01-05T10:00:00Z -n 2 '0 9 * * 1-5'
./bin/{{ package_name }} --explain -n 1 '0 9 * * 1-5'
./bin/{{ package_name }} '0 0 29 2 *'        # the next leap day
```

Fields are the classic five: minute, hour, day of month, month, day of week.
Each accepts `*`, a number, a name (`JAN`, `MON`), a list (`1,15`), a range
(`1-5`) and a step (`*/15`). Sunday is both `0` and `7`.

When day of month and day of week are *both* restricted they combine with OR, so
`0 0 13 * 5` fires on every Friday and on every 13th — the traditional rule, not
the least surprising one.

Exit codes: `0` success, `1` the expression can never fire (such as 31 February),
`2` bad usage or a malformed expression.

## Layout

- `src/cronkit/schedule.clj` — parsing, matching, and the unit-skipping search.
- `src/cronkit/options.clj` — argument parsing.
- `src/cronkit/cli.clj` — the command: argv plus an io record in, exit code out.
- `src/cronkit/main.clj` — the only place that touches the terminal.
- `test/cronkit/` — schedule, options and CLI tests.

## Tests

```sh
clojure -M:test -m cronkit.run-tests
```
