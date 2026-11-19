# {{ title }}

{{ description }}

Unsigned LEB128 varints — the variable-length integer encoding protobuf, DWARF
and WebAssembly use — in about sixty lines of Zig with no dependencies.
Encoding and decoding live in `src/varint.zig` as pure functions, so the tests
drive them directly and `src/main.zig` stays a thin argv/stdio shell.

## Usage

```sh
zig build
./zig-out/bin/{{ package_name }} encode 300        # 172 2
./zig-out/bin/{{ package_name }} encode 0          # 0
./zig-out/bin/{{ package_name }} decode 172 2      # 300
./zig-out/bin/{{ package_name }} decode 172,2      # 300
```

`encode` prints the bytes space separated; `decode` accepts space or comma
separated bytes, makes sure the last byte has no continuation bit set
(`truncated`) and that no bytes follow it (`trailing`).

```sh
zig build test
```

Exit codes: `0` success or `--help`, `2` usage error (unknown command,
non-numeric argument, out-of-range byte, no arguments). A `decode` that cannot
represent the value prints the error and exits `2` as well.

## Layout

- `src/varint.zig` — `encodeUleb128`, `decodeUleb128`, `VarintError`
  (`Overflow`, `Truncated`, `Trailing`) plus the round-trip test vectors.
- `src/main.zig` — argv parsing (`encode`, `decode`, `--help`), printing, exit codes.
- `build.zig` / `build.zig.zon` — `zig build`, `zig build test`, `zig build run`.

## Package identity

`build.zig.zon` pins `.name = .varint` and a matching `.fingerprint`. Zig 0.17
rejects a fingerprint that does not hash the package name, and the value embeds
the absolute build path, so a scaffold cannot compute one per project. If you
publish this package, give it your own name: change `.name`, delete the
`.fingerprint` line, run `zig build`, and paste back the value Zig suggests.

## License

MIT — see [LICENSE](LICENSE).
