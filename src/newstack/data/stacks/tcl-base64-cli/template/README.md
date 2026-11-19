# {{ title }}

{{ description }}

A base64 and base64url encoder written against plain byte strings: no
packages, no C extensions, just `tclsh`.

## Usage

```sh
./bin/{{ package_name }} encode -t foobar          # Zm9vYmFy
./bin/{{ package_name }} decode -t Zm9vYmFy        # foobar
printf 'hello' | ./bin/{{ package_name }} encode   # aGVsbG8=
./bin/{{ package_name }} encode --hex -t 00ff      # AP8=
./bin/{{ package_name }} decode --hex -t AP8=      # 00ff
./bin/{{ package_name }} encode --url --no-padding -t '<<??>>'   # PDw_Pz4-
```

Options: `--url` (URL-safe alphabet), `--no-padding`, `--hex`, `-t/--text`,
`-h/--help`, `-V/--version`. With no `-t` and no `FILE`, stdin is read.
Exit codes: `0` success, `1` invalid input or an unreadable file, `2` usage.

## Layout

- `lib/base64.tcl` — the codec plus hex helpers.
- `lib/options.tcl` — a hand-written argv parser.
- `lib/runner.tcl` — encode/decode wiring, I/O behind a dictionary.
- `main.tcl` — the only file that touches files, stdin and exit.
- `tests/` — a dependency-free harness and three suites.

## Tests

```sh
tclsh tests/run.tcl
sh smoke.sh
```
