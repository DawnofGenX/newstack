# {{ title }}

A Free Pascal command-line generator for RFC 4122 version 4 UUIDs. The
generator, the parser, the option parser and the CLI each live in their own
unit; the CLI takes streams instead of writing to stdout directly.

## Usage

```sh
make
./bin/{{ npm_name }}
./bin/{{ npm_name }} -n 3
make test
```

`-n COUNT` accepts 1 through 100. Exit status is 0 on success and 2 on a usage
error. Parsed UUIDs keep the canonical lowercase hex form with dashes in the
standard positions, version nibble 4 and variant bits 10.

## Layout

- `src/uuidgen.pas` — v4 generation and strict parsing
- `src/uuidopts.pas` — hand-written option parser
- `src/uuidrunner.pas` — stream-injected CLI
- `tests/run_tests.pas` — dependency-free assertions
