# {{ title }}

{{ description }}

A Lua 5.4 command line tool that reads delimited text, selects columns and writes
it back out as CSV, TSV or JSON. Parsing lives in `src/csval/parse.lua` (pure, no
I/O), column resolution in `src/csval/select.lua`, rendering and JSON encoding in
`src/csval/format.lua`, and `bin/{{ npm_name }}` is the thin entry point that owns
argv, stdout/stderr and the exit code.

## Usage

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} data.csv
$ ./bin/{{ npm_name }} -c id,amount data.csv
$ ./bin/{{ npm_name }} -o json data.csv
$ cat data.csv | ./bin/{{ npm_name }} -o tsv --no-header
```

Options:

| flag | meaning |
| ---- | ------- |
| `-c, --columns LIST` | comma-separated column names or 1-based positions |
| `-d, --delimiter CHAR` | input delimiter: one byte, or `tab` (default `,`) |
| `-o, --output FORMAT` | `csv`, `tsv` or `json` (default `csv`) |
| `--no-header` | treat the first row as data, not as column names |
| `-h, --help` | show help and exit 0 |
| `-V, --version` | show the version and exit 0 |

With a header row, `-o json` emits an array of objects keyed by the selected
column names; with `--no-header` it emits an array of arrays:

```console
$ printf 'id,name\n1,alpha\n' | ./bin/{{ npm_name }} -o json
[{"id":"1","name":"alpha"}]
```

## Layout

```
bin/{{ npm_name }}             entry point: argv -> help | usage | conversion
src/csval.lua                   module facade: require("csval")
src/csval/parse.lua             parse(): RFC 4180 text -> rows, width check
src/csval/select.lua            resolve(): column names/positions -> indexes
src/csval/format.lua            render(): rows -> delimited text, encode(): JSON
src/csval/options.lua           parse(): argv -> options table
spec/harness.lua                hand-rolled describe/it/eq, no dependencies
spec/run.lua                    runner: lua5.4 spec/run.lua
spec/parse_spec.lua             quoting, CRLF, ragged rows
spec/select_spec.lua            column resolution and projection
spec/options_spec.lua           every parser branch
spec/cli_spec.lua               the real script: stdout and exit codes
```

No dependencies: only the Lua 5.4 standard library, no luarocks and no network.

## Requirements

Lua 5.4. The interpreter is called `lua5.4` on Debian/Ubuntu, which is the name in
the shebang, so `./bin/{{ npm_name }}` runs without a `chmod` dance.

## CSV semantics

RFC 4180 with the usual relaxations: doubled quotes inside a quoted field become
one quote, a delimiter or newline inside quotes is data, CRLF outside quotes ends
a row, and a file that ends without a trailing newline still yields its last row.
Rows must all be the same width — a ragged row is reported with its line number
(`error: line 2: 1 field(s), expected 2`) rather than padded with empty columns.
Output quotes a field only when it contains the delimiter, a quote, a newline or
leading/trailing spaces.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` and `--version` |
| 1 | the input could not be read, or it is not valid delimited text |
| 2 | usage error: unknown flag, unknown column, bad option value |

## Test

```console
$ lua5.4 spec/run.lua
```

The runner prints one `ok` line per test and ends with `N passed, M failed`;
`spec/cli_spec.lua` spawns `bin/{{ npm_name }}` through `io.popen`, so the exit
codes are the ones a shell would see.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.
