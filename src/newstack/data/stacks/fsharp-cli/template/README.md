# {{ title }}

{{ description }}

A small F# 8 / .NET 8 command line tool: counting lives in a library
(`Counts.ofString`, `Counts.ofBytes`) so tests drive it directly, `Options.parse`
turns argv into a `Mode` discriminated union plus a `Status`, and `Program.fs` is
the only file that prints or sets an exit code. xUnit runs the suite, including
tests that launch the built binary and assert its exit codes as a contract.

## Layout

```
App.fsproj                                  exe: the thin entry point
Program.fs                                  prints, selects the exit code, calls exit
Core/Core.fsproj                            library with the pure logic
Core/Counts.fs                              line / word / byte record and counting
Core/Options.fs                             hand-rolled argv parsing and help text, no I/O
Tests/Tests.fsproj                          xUnit suite
Tests/CountsTests.fs                        counting: trailing newline, whitespace, bytes
Tests/OptionsTests.fs                       parsing: modes, conflicts, --, unknown flags
Tests/CliExitCodes.fs                       launches the built exe, asserts 0 / 1 / 2
.github/workflows/ci.yml                    restore, build, test, CLI smoke on push
```

Compile order matters in F#: `Core.fsproj` lists `Counts.fs` before `Options.fs`,
and each project lists its files explicitly in the `.fsproj`.

## Why there is no `.sln`

`App.fsproj` sits at the repository root because that is the marker `newstack
adopt` looks for. A solution file next to a project file makes bare
`dotnet build` fail with `MSB1011` (it cannot guess which one you meant), so the
commands below name the project instead. `dotnet test` on the root project would
only see the exe, so it names the test project too.

## Build

```console
$ dotnet build App.fsproj --nologo
```

## Run

```console
$ dotnet run --project App.fsproj -- --help
$ dotnet run --project App.fsproj -- README.md
$ printf 'one two\nthree\n' | dotnet run --project App.fsproj -- -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. `--` ends option parsing, and `-` reads standard input.

## Exit-code contract

| Code | Meaning                                              |
| ---- | ---------------------------------------------------- |
| `0`  | counted every file (or stdin)                        |
| `1`  | a file could not be read; the rest were still counted |
| `2`  | bad usage: unknown flag or two conflicting modes     |

`--help` and `--version` exit `0`. Bad usage prints the error and the usage
block to stderr, so a pipeline never sees it on stdout.

## Test

```console
$ dotnet test Tests/Tests.fsproj --nologo
```

`CliExitCodes.fs` finds the exe in `bin/Debug/net8.0` (or `bin/Release/net8.0`)
and starts it as a process, so the exit codes are proven by the shipped binary
rather than by calling `Program.main` in process.

## Rename

The project name is baked into three places; change them together:

1. `App.fsproj` — `<AssemblyName>` (the exe name) and `<RootNamespace>`.
2. `Core/Core.fsproj` and `Tests/Tests.fsproj` — `<AssemblyName>` and
   `<RootNamespace>` (the namespace must stay a valid F# identifier: letters,
   digits and underscores, no hyphens).
3. The `namespace` / `module` declarations in `Core/*.fs`, `Program.fs` and
   `Tests/*.fs`, and the program name string in `Program.fs`.

## License

MIT — see [LICENSE](LICENSE).
