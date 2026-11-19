# {{ title }}

{{ description }}

JSON Lines is the cheapest format for append-only record streams, but reading it
by hand is miserable. This tool treats it like a table you can query: project
columns, filter with comparisons, sort, and summarise — while keeping the output
valid JSON Lines.

## Usage

```sh
./bin/{{ package_name }} rows.jsonl                              # canonical JSONL
./bin/{{ package_name }} -f id,user.name rows.jsonl              # project columns
./bin/{{ package_name }} --where score --gt 9 rows.jsonl         # filter
./bin/{{ package_name }} --where user.name --match '^c' rows.jsonl
./bin/{{ package_name }} --sort score --numeric --reverse rows.jsonl
./bin/{{ package_name }} --stats score rows.jsonl                # count/sum/mean/min/max
./bin/{{ package_name }} --count rows.jsonl                      # how many records?
```

Paths address nested data: `user.name`, `tags[0]`, `a.b[2].c`.
A bare `--where PATH` keeps records whose value is present, non-empty, non-zero
and not `false`. Blank lines are skipped.
Exit codes: `0` success, `1` bad input (bad JSON, unreadable file), `2` usage.

One query, one pass: the file is read once, filtered, sorted in memory and
written back out.

## Layout

- `lib/Jsonl.pm` — decoding, path parsing, projections, scalar helpers.
- `lib/Jsonl/Query.pm` — where clauses and the numeric-vs-text comparison rule.
- `lib/Jsonl/Stats.pm` — count/sum/mean/min/max over one numeric column.
- `lib/Jsonl/Options.pm` — argument parsing; unknown options never reach a command.
- `bin/{{ npm_name }}` — the CLI; all exit codes are decided here.

## Tests

```sh
perl Makefile.PL && make test
```
