# {{ title }}

{{ description }}

Base64 in the two alphabets that actually matter — the standard one
(`+/`) and the URL-safe one (`-_`) — with optional `=` padding and
whitespace-tolerant decoding. Nim standard library only, no dependencies.

## Usage

```sh
nimble build
./{{ package_name }} encode hello          # aGVsbG8=
./{{ package_name }} decode aGVsbG8=       # hello
./{{ package_name }} encode --no-padding hello   # aGVsbG8
./{{ package_name }} encode --url '???'    # Pz8_
printf 'hello' | ./{{ package_name }} encode   # aGVsbG8=
```

Options: `--url`, `--no-padding`, `--standard`, `-h/--help`, `-V/--version`.
Exit codes: `0` success, `1` the input is not valid base64, `2` usage error.

## Layout

- `src/{{ package_name }}/base64x.nim` — pure codec (`encodeBytes`, `encodeText`,
  `decodeText`, `withoutPadding`, `toUrlSafe`, `fromUrlSafe`).
- `src/{{ package_name }}/options.nim` — hand-written argv parser.
- `src/{{ package_name }}.nim` — entry point, reads standard input when no
  value is given.
- `tests/test_all.nim` — codec, parser and binary exit-code suites.

## Tests

```sh
nimble test
sh smoke.sh
```
