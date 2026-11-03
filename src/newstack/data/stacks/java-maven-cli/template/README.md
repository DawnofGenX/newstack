# {{ title }}

{{ description }}

A small Java 21 command line tool: counting lives in plain classes
(`TextStat`, `Counts`) so tests drive it directly, and `App` is a thin entry
point that owns `System.exit`. Maven builds the jar and runs the JUnit 5 suite.

## Layout

```
pom.xml                            Java 21, JUnit 5, jar manifest with Main-Class
src/main/java/{{ package_name }}/Counts.java   line / word / byte record
src/main/java/{{ package_name }}/TextStat.java pure counting, no I/O
src/main/java/{{ package_name }}/Options.java  hand-rolled argv parsing and help text
src/main/java/{{ package_name }}/Cli.java      reads files or stdin, prints, returns an exit code
src/main/java/{{ package_name }}/App.java      main(): System.exit(new Cli(stdin).run(...))
src/test/java/{{ package_name }}/             JUnit 5 tests for counting, parsing and exit codes
```

No runtime dependencies: argument parsing is hand-rolled, and JUnit 5 is the
only test dependency.

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
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ mvn -B test
```

## License

MIT — see [LICENSE](LICENSE).
