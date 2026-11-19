# {{ title }}

{{ description }}

A JSON reader and writer in plain Lua 5.4, with no LuaRocks and no C
extensions: recursive-descent parsing with byte offsets in error messages,
compact/pretty/canonical output, and a `--get` path walker.

## Usage

```sh
printf '{"b":2,"a":1}' | ./bin/{{ package_name }}            # {"b":2,"a":1}
printf '{"b":2,"a":1}' | ./bin/{{ package_name }} --canonical # {"a":1,"b":2}
printf '{"a":{"b":[5]}}' | ./bin/{{ package_name }} --get 'a.b[0]'   # 5
./bin/{{ package_name }} --pretty data.json
./bin/{{ package_name }} --check data.json                  # valid
```

Options: `--pretty`, `--compact`, `--canonical`, `--get PATH`, `--check`,
`-h/--help`, `-V/--version`.
Exit codes: `0` success, `1` invalid JSON or a missing path/file, `2` usage.

## Layout

- `src/ljson/decode.lua` — the parser, plus the `null` sentinel that keeps
  `[1,null,3]` three elements long.
- `src/ljson/encode.lua` — serialiser with pretty and canonical modes.
- `src/ljson/init.lua` — public surface, argv parser and path walker.
- `bin/{{ package_name }}` — entry point.
- `spec/` — dependency-free harness and four suites.

## Tests

```sh
lua5.4 spec/run.lua
sh smoke.sh
```
