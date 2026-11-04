# {{ title }}

{{ description }}

A minimal Scala 3 command line tool built with **scala-cli**: there is no
`build.sbt`, no `pom.xml` and no build server. `project.scala` holds three
`//> using` directives (Scala version, main class, the one test dependency) and
that is the whole build definition.

The code is split the way the other newstack CLIs are: counting is pure and
knows nothing about I/O (`src/main/scala/textstat/Counts.scala`), parsing turns
`argv` into a decision (`Options.scala`), `Runner.scala` turns that decision
into output and an exit code against an `Io` interface, and `Main.scala` is the
only file that touches the real process — `System.in`, `Files.readAllBytes` and
`sys.exit`.

## Layout

```
project.scala                                scala-cli directives: Scala 3.3.6, main class, munit
bin/{{ npm_name }}                           wrapper: `scala-cli run . --server=false --main-class textstat.Main`
src/main/scala/textstat/Counts.scala         Counts.ofBytes(bytes) and the aligned row layout — pure
src/main/scala/textstat/Options.scala        Options.parse(argv): figures/files/status — pure
src/main/scala/textstat/Runner.scala         Runner.run(argv, io): Int, the exit-code contract
src/main/scala/textstat/Main.scala           the real Io: stdin/stdout/stderr and sys.exit
src/test/scala/CountsSuite.scala             wc semantics: trailing newline, whitespace runs, UTF-8 bytes
src/test/scala/OptionsSuite.scala            every parser branch: clusters, `--`, `-`, help, errors
src/test/scala/RunnerSuite.scala             exit codes and layout, asserted against a fake Io
```

`Runner.run` takes an `Io` rather than reading the world directly, so the exit
contract — and the exact spacing of the output — is tested without spawning a
process or touching the filesystem.

## Requirements

A JDK (21 here, installed through `actions/setup-java` in CI) and **scala-cli**
1.18.0, a single binary you can drop on your `PATH`:

```console
$ curl -sSLf -o scala-cli.gz https://github.com/VirtusLab/scala-cli/releases/download/v1.18.0/scala-cli-x86_64-pc-linux.gz
$ gzip -d scala-cli.gz && chmod +x scala-cli && sudo mv scala-cli /usr/local/bin/
$ scala-cli version
```

The Scala compiler, the standard library and munit are fetched by scala-cli
(coursier) on the first build and cached under `~/.cache/coursier`; after that
builds and tests are offline.

## Build

```console
$ scala-cli compile .
```

`--server=false` (which the wrapper passes) runs the compiler in-process instead
of starting the Bloop build server. It is a little slower per invocation but
leaves no daemon behind, which is what you want in CI.

## Test

```console
$ scala-cli test .
```

Three munit suites, no custom harness: `CountsSuite` pins the `wc` semantics,
`OptionsSuite` covers every branch of the parser, and `RunnerSuite` asserts the
0/1/2 exit contract and the column layout through a fake `Io`.

## Run

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} README.md
$ cat README.md | ./bin/{{ npm_name }} -w
```

Output is `wc`-style: lines, words, bytes, then the path. Every column is
right-aligned to the widest figure in the output, and with more than one file a
`total` line is printed.

```console
$ printf 'alpha beta\ngamma\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  3 17 sample.txt
```

`-l`, `-w` and `-c` combine in any order (and cluster, as in `-lw`); with no
counting flag all three figures are printed. Lines follow `wc -l`: they count
`\n` bytes, so a last line without a trailing newline is not counted. Bytes are
raw bytes, so `héllo wörld` is 13 bytes, not 11.

The wrapper runs the project in place, so the first invocation after a clean
checkout compiles and prints scala-cli's progress on stderr.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read (the other files are still counted) |
| 2    | usage error: unknown option |

`Runner.run` *returns* these codes; only `Main` calls `sys.exit`, which is what
lets `RunnerSuite` assert them directly.

## Packaging

When you want a real binary instead of a wrapper, scala-cli can build an
assembly jar with a launcher:

```console
$ scala-cli package . --assembly -o textstat
$ ./textstat sample.txt
```

## Naming

The package is `textstat` and the command is `bin/{{ npm_name }}`; the usage line
prints the command name from `Runner.program`, so rename the wrapper and that
constant together. To rename the *package*, move `src/main/scala/textstat/` and
change the `package textstat` line in each file — the `mainClass` directive in
`project.scala` follows it.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.
