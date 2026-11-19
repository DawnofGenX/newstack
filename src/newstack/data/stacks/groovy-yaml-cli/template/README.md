# {{ project_name }}

YAML subset reader that prints flattened keys.

## Usage

```
printf 'a:\n  b: 1\n  c: hello\n' | ./bin/{{ npm_name }}
# a.b: 1
# a.c: hello
```

Exit codes: 0 success, 1 error, 2 usage error.