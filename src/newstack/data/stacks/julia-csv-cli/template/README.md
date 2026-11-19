# {{ title }}

{{ description }}

A CSV reader and reporter on the Julia standard library: RFC 4180 parsing,
minimal-quote rendering, column selection, per-column statistics and a JSON
view. No dependencies.

## Usage

```sh
julia --project=. bin/{{ package_name }}.jl data.csv               # echo the table
julia --project=. bin/{{ package_name }}.jl --json data.csv        # array of objects
julia --project=. bin/{{ package_name }}.jl --columns city,name data.csv
julia --project=. bin/{{ package_name }}.jl --summary score data.csv
printf 'a;b\n1;2\n' | julia --project=. bin/{{ package_name }}.jl --delimiter ';'
```

Options: `--print` (default), `--json`, `--summary COL`, `--columns LIST`,
`--delimiter D`, `--out-delimiter D`, `-h/--help`, `-V/--version`.
Exit codes: `0` success, `1` bad input, `2` usage.

## Layout

- `src/csv.jl` — the parser, the renderer, column selection, statistics, JSON.
- `src/options.jl` — a hand-rolled argv parser.
- `src/CsvKit.jl` — the module that includes both.
- `bin/{{ package_name }}.jl` — the only file that touches a device or exits.
- `test/runtests.jl` — the suite, including child-process exit-code checks.

## Tests

```sh
JULIA_PKG_OFFLINE=true julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. test/runtests.jl
sh smoke.sh
```
