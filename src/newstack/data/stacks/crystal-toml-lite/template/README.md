# {{ project_name }}

Parse a TOML subset and print flattened key = value lines.

## Usage

```sh
crystal build -o bin/{{ npm_name }} src/main.cr
./bin/{{ npm_name }} config.toml
./bin/{{ npm_name }} --help
```

Exit codes: 0 success, 1 unreadable input, 2 usage or parse error.