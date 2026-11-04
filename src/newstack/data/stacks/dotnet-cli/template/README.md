# {{ title }}

{{ description }}

A small .NET 8 / C# 12 command line tool: counting lives in a pure library unit
(`TextStat`, `Counts`) so tests drive it directly, argument parsing is hand-rolled
(`Options`), and the console app is a thin entry point that owns the exit code.
xUnit runs the test suite and the solution file ties the app and test projects
together.

## Layout

```
{{ npm_name }}.sln                              solution: build and test the whole tree
{{ npm_name }}.csproj                           the console app (net8.0, nullable, implicit usings)
Program.cs                                      top-level entry point
src/Counts.cs                                   line / word / byte record
src/TextStat.cs                                 pure counting, no I/O
src/Options.cs                                  hand-rolled argv parsing and help text
src/Cli.cs                                      reads files or stdin, prints, returns an exit code
tests/                                          xUnit tests for counting, parsing and exit codes
.github/workflows/ci.yml                        restore, build, test, exit-code proof on push
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
$ dotnet run -- --help
$ dotnet run -- README.md
$ printf 'one two\nthree\n' | dotnet run -- -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ dotnet test --nologo
```

## License

MIT — see [LICENSE](LICENSE).
