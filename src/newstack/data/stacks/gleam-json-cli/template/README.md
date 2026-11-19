# {{ project_name }}

JSON compactor / prettifier with a hand-written recursive-descent parser.

## Usage

Compact (default):

```
printf '{"a": 1, "b": [2, 3]}' | ./bin/{{ npm_name }}
# {"a":1,"b":[2,3]}
```

Pretty-print:

```
printf '{"a":1}' | ./bin/{{ npm_name }} pretty
# {
#   "a": 1
# }
```

Exit codes: 0 success, 1 parse error, 2 usage error.