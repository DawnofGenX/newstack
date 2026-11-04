# {{ npm_name }}

Reports over a JSON access log, written as plain [jq](https://jqlang.github.io/jq/)
programs and wrapped in a small shell command with a tested exit-code contract.

Every report is one file in `filters/`. There is no glue: the command finds the
file, runs it with `jq -c`, and prints what jq prints. That means any report in
this project can be reproduced by hand:

```sh
jq -c -f filters/top-paths.jq data/sample.json
./bin/{{ npm_name }} run top-paths data/sample.json
```

## Quick start

```sh
make lint       # every filter must compile
make test       # 60+ assertions over the filters and the command line
make report     # print all five reports for the sample log
./bin/{{ npm_name }} --help
```

## The command

```
Usage: {{ npm_name }} COMMAND [ARG]...

  run FILTER [FILE]   apply filters/FILTER.jq to FILE (default: standard input)
  filters             list the available filters, one per line
  lint [DIR]          check that every filter in DIR (default: filters/) compiles
  help                show this message
```

Exit status is part of the contract:

| status | meaning |
| ------ | ------- |
| 0 | the report was printed |
| 1 | the input could not be read, or is not valid JSON |
| 2 | usage error (unknown command, unknown filter, missing argument) |

## The filters

The sample log in `data/sample.json` is six requests from two days.

| filter | question it answers |
| ------ | ------------------- |
| `status-counts` | how many requests per status code, ordered by code |
| `top-paths` | the five busiest paths, ties broken by path |
| `slowest` | the five slowest requests, ties broken by path |
| `bytes-by-day` | bytes served per calendar day |
| `error-rate` | one object: total, 5xx count, and the percentage |

```sh
$ ./bin/{{ npm_name }} run status-counts data/sample.json
[{"status":200,"requests":3},{"status":201,"requests":1},{"status":404,"requests":1},{"status":500,"requests":1}]

$ ./bin/{{ npm_name }} run error-rate < data/sample.json
{"total":6,"errors":1,"error_rate":16.7}
```

The input is a JSON array of objects with `time`, `method`, `path`, `status`,
`bytes` and `ms`. An empty array is a valid log with no traffic: every filter
answers instead of dividing by zero.

## Adding a filter

1. Write `filters/<name>.jq`. Its input is the whole log array, so a report
   usually starts with `group_by` or `sort_by`.
2. Run `./bin/{{ npm_name }} lint` — a filter that does not compile is a
   compile error here, before any data is involved.
3. Add its answer to `tests/filters_test.sh`. The expected JSON is written by
   hand there, not captured from the tool, so a change in behaviour is a
   deliberate edit to the test.

## Layout

```
bin/{{ npm_name }}        wrapper: finds the project root, then runs lib/cli.sh
lib/cli.sh            argument parsing, filter lookup, exit-code mapping
filters/*.jq          one report each, plain jq
data/sample.json      the sample access log
tests/                harness.sh, filters_test.sh, cli_test.sh, run_tests.sh
```

## Requirements

`jq` 1.6 or newer, `bash`, and `make` if you want the shortcuts. Nothing is
downloaded at build time.

## License

MIT — see `LICENSE`.
