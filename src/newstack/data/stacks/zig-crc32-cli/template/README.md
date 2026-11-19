# {{ title }}

{{ description }}

CRC-32 with the IEEE 802.3 polynomial — the same checksum `gzip`, `zlib` and
`cksum -o 3` use — in about thirty lines of Zig, with no dependencies.

## Usage

```sh
zig build
./zig-out/bin/{{ package_name }} --string 123456789        # cbf43926
./zig-out/bin/{{ package_name }} --string ""               # 00000000
./zig-out/bin/{{ package_name }} --file README.md          # checksum of a file
./zig-out/bin/{{ package_name }} --string abc --check 352441c2   # ok 352441c2
```

Options: `--string TEXT`, `--file PATH`, `--check HEX`, `-h/--help`.
Exit codes: `0` success or matching `--check`, `1` unreadable file or
mismatched checksum, `2` usage error.

## Layout

- `src/crc32.zig` — `update`, `hash`, `toHex` and the CRC test vectors.
- `src/main.zig` — argv parser (pure, so it is tested directly) and printing.
- `build.zig` / `build.zig.zon` — `zig build`, `zig build test`, `zig build run`.

## Tests

```sh
zig build test
sh smoke.sh
```
