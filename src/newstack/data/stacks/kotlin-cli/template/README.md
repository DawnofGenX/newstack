# {{ title }}

{{ description }}

A small Kotlin/JVM 21 command line tool: counting lives in a plain object
(`TextStat`) so tests drive it directly, and `Cli` is a thin entry point that
parses argv, prints and returns the exit code — `main()` is the only place that
calls `exitProcess`. Maven builds the jar and runs the JUnit 5 suite.

## Why Maven and not Gradle

Gradle projects ship a binary `gradle-wrapper.jar`. newstack templates are
plain text, so a Gradle starter would either be missing its wrapper or fake it.
Maven needs no wrapper binary, so `mvn` on the PATH is enough.

## Layout

```
pom.xml                                   Kotlin/JVM 21, JUnit 5, shaded jar with Main-Class
src/main/kotlin/{{ package_name }}/Counts.kt   line / word / byte holder
src/main/kotlin/{{ package_name }}/TextStat.kt pure counting, no I/O
src/main/kotlin/{{ package_name }}/Options.kt  hand-rolled argv parsing and help text
src/main/kotlin/{{ package_name }}/Cli.kt      reads files or stdin, prints, returns an exit code
src/main/kotlin/{{ package_name }}/Main.kt     main(): exitProcess(Cli(System.`in`).run(...))
src/test/kotlin/{{ package_name }}/             JUnit 5 tests for counting, parsing and exit codes
```

`kotlin-stdlib` is the only runtime dependency; argument parsing is hand-rolled
and JUnit 5 is the only test dependency. The shade plugin bundles the stdlib
into the jar so `java -jar` works without a classpath.

## Build

```console
$ mvn -B package
```

The jar is `target/{{ npm_name }}.jar`.

## Run

```console
$ java -jar target/{{ npm_name }}.jar --help
$ java -jar target/{{ npm_name }}.jar README.md
$ printf 'one two\nthree\n' | java -jar target/{{ npm_name }}.jar -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Exit codes are part of the contract: `0` success, `1` an unreadable
file, `2` bad usage.

## Test

```console
$ mvn -B verify
```

## License

MIT — see [LICENSE](LICENSE).
