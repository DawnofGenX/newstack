# {{ title }}

{{ description }}

A `wc -l -w -c` clone in Swift: a pure counting core, a hand-rolled argv
parser, and a thin executable that reads real files and stdin. No external
dependencies — just SwiftPM and XCTest.

## Layout

| Path | Purpose |
| --- | --- |
| `Package.swift` | SwiftPM manifest: `TextStat` library, `TextStatCLI` executable, `TextStatTests` |
| `Sources/TextStat/Counts.swift` | Pure counting: `ofBytes`, `add`, `wc`-style row layout |
| `Sources/TextStat/Options.swift` | Hand-rolled argv parser: `-l/-w/-c`, `--lines/--words/--bytes`, `-h/--help`, `-V/--version`, `--`, `-` |
| `Sources/TextStat/CLI.swift` | `run(_:io:) -> Int32` against an injected `IO` of closures |
| `Sources/TextStatCLI/main.swift` | The only file that touches the real process: files, stdin, stdout, stderr, `exit` |
| `Tests/TextStatTests/` | XCTest suites asserting through the injected `IO` |
| `bin/{{ npm_name }}` | Wrapper that builds in release mode (progress on stderr) and execs the binary |

## Build, test, run

```sh
swift build
swift test
./bin/{{ npm_name }} --help
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | success, `--help`, `--version` |
| `1` | a file could not be read (`error: cannot open '<path>'`); the other files are still counted |
| `2` | usage error (`<program>: unknown option: --bogus`, then a hint to run `--help`) |

## `wc` semantics

- A **line** is a `\n` byte (10). A final line without a trailing newline is
  not counted, exactly like `wc -l`.
- A **word** is a maximal run of non-whitespace bytes, where whitespace is
  space, tab, newline, vertical tab, form feed, and carriage return.
- **Bytes** are raw bytes, not characters: a UTF-8 multibyte sequence counts
  as many bytes as it occupies, so the numbers match `wc -c` on the same file.
- With no flag, all three figures are printed. With more than one operand, a
  `total` row is appended. Every figure is right-aligned to the widest figure
  printed anywhere in the output, with a single space between columns and the
  label last.

## Sample transcript

```console
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3 -
$ ./bin/{{ npm_name }} a.txt b.txt
 2  3 17 a.txt
 1  1  4 b.txt
 3  4 21 total
$ ./bin/{{ npm_name }} --bogus
{{ npm_name }}: unknown option: --bogus
Try '{{ npm_name }} --help' for more information.
$ echo $?
2
```
