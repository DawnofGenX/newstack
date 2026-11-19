# JSONPath Lite

A small, dependency-free JSONPath evaluator for SBCL. It parses a JSON document with
`lib/json.lisp` and evaluates a query containing dot-separated keys, `[*]` wildcards on
arrays, and `..` recursive descent. Each match is printed on its own line in compact JSON
form.

## Usage

```sh
sbcl --script tests/run-tests.lisp
./bin/{{ npm_name }} FILE PATH
./bin/{{ npm_name }} --help
```

Examples against `testdata/sample.json`:

```sh
$ ./bin/{{ npm_name }} testdata/sample.json '$.a.b'
42

$ ./bin/{{ npm_name }} testdata/sample.json '$.arr[*]'
1
2
3

$ ./bin/{{ npm_name }} testdata/sample.json '$.deep..name'
"root"
```

Exit codes: `0` when the query succeeds (including zero matches), `1` when the JSON is
malformed or the file cannot be read, `2` for a missing FILE or PATH argument.

## Supported paths

| Query | Meaning |
| ----- | ------- |
| `$` | the whole document |
| `$.a.b` | dot-separated object keys |
| `$.arr[*]` | every element of an array |
| `$..key` | recursive descent: every `key` anywhere below the root |

Unsupported path syntax signals an error; there is no silent partial match.

## Layout

- `lib/json.lisp` — JSON reader, compact writer, and the path evaluator
- `main.lisp` — CLI entry point; all errors go to stderr
- `tests/run-tests.lisp` — pinned known-value assertions plus a malformed-JSON case
- `bin/{{ npm_name }}` — shell wrapper invoking `sbcl --script`
