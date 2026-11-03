# {{ title }}

{{ description }}

A small .NET 8 / C# 12 command line tool: counting lives in a class library
(`TextStat`, `Counts`) so tests drive it directly, and the console app is a thin
entry point that owns the exit code. xUnit runs the test suite and the solution
file ties all three projects together.

## Layout

```
{{ npm_name }}.sln                              solution: build and test the whole tree
Directory.Build.props                           net8.0, C# 12, nullable, implicit usings
src/{{ npm_name }}.Core/Counts.cs               line / word / byte record
src/{{ npm_name }}.Core/TextStat.cs             pure counting, no I/O
src/{{ npm_name }}.Cli/Options.cs               hand-rolled argv parsing and help text
src/{{ npm_name }}.Cli/Cli.cs                   reads files or stdin, prints, returns an exit code
src/{{ npm_name }}.Cli/Program.cs               top-level entry point
tests/{{ npm_name }}.Tests/                     xUnit tests for counting, parsing and exit codes
.github/workflows/ci.yml                        restore, build, test, CLI smoke on push
```

No runtime dependencies: argument parsing is hand-rolled, and the test project's
only packages are `xunit`, `xunit.runner.visualstudio` and `Microsoft.NET.Test.Sdk`,
all pinned to exact versions.

## Build

```console
$ dotnet build --nologo
```

## Run

```console
$ dotnet run --project src/{{ npm_name }}.Cli -- --help
$ dotnet run --project src/{{ npm_name }}.Cli -- README.md
$ printf 'one two\nthree\n' | dotnet run --project src/{{ npm_name }}.Cli -- -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ dotnet test --nologo
```

## License

MIT — see [LICENSE](LICENSE).
