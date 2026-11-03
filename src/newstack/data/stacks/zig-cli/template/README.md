# {{ title }}

{{ description }}

A minimal Zig 0.17 command line tool: counting lives in `src/counting.zig`
(pure functions, no I/O) so the tests drive it directly, and `src/main.zig` is
a thin entry point that owns argv, stdout/stderr and the exit code.

## Layout

```
build.zig              `zig build` installs the exe, `zig build test` runs both test binaries
build.zig.zon          package manifest (name, version, fingerprint, minimum Zig version)
src/counting.zig       count(): lines, words, bytes — the only place that decides an answer
src/main.zig           parse(): argv → help | usage | count, plus main() and the usage text
```

No dependencies: `build.zig.zon` declares an empty `dependencies` table.

## Build

```console
$ zig build
```

The binary is `zig-out/bin/{{ package_name }}`.

## Run

```console
$ ./zig-out/bin/{{ package_name }} --help
$ ./zig-out/bin/{{ package_name }} README.md
```

Output is wc-style, right-aligned: lines, words, bytes, then the path.

```
      3       5      30 sample.txt
```

Exit codes are part of the contract:

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` |
| 1    | the file could not be read |
| 2    | usage error: unknown flag, missing or extra arguments |

## Test

```console
$ zig build test
```

The build wires two test binaries: one rooted at `src/counting.zig` and one at
`src/main.zig`, so `test` blocks in either file are run.

## Package identity

`build.zig.zon` pins `.name = .textstat` and a matching `.fingerprint`. Zig 0.17
rejects a fingerprint that does not hash the package name, and the value embeds
the absolute build path, so a scaffold cannot compute one per project. If you
publish this package, give it your own name: change `.name`, delete the
`.fingerprint` line, run `zig build`, and paste back the value Zig suggests.

## License

MIT — see [LICENSE](LICENSE).
