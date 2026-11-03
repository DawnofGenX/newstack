# {{ title }}

{{ description }}

A small Dart 3 command line tool: counting lives in `lib/src` with no I/O, and
`bin/{{ npm_name }}.dart` is a thin entry point that owns output and exit
codes. Tests run on `package:test`.

## Layout

```
pubspec.yaml                      Dart 3, `test` and `lints` as dev dependencies
analysis_options.yaml             package:lints/recommended.yaml, enforced in CI
lib/{{ package_name }}.dart                  the public library, re-exporting lib/src
lib/src/counts.dart               line / word / byte value type
lib/src/text_stat.dart            pure counting, no I/O
lib/src/options.dart              hand-rolled argv parsing and help text
bin/{{ npm_name }}.dart                    main(): parses, reads, prints, sets exitCode
test/text_stat_test.dart          counting behaviour
test/options_test.dart            parsing behaviour
test/cli_test.dart                exit codes, through the real script
```

No runtime dependencies: argument parsing is hand-rolled, and `test` plus
`lints` are the only dev dependencies.

## Run

```console
$ dart pub get
$ dart run bin/{{ npm_name }}.dart --help
$ dart run bin/{{ npm_name }}.dart README.md
$ printf 'one two\nthree\n' | dart run bin/{{ npm_name }}.dart -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

The package name is `{{ package_name }}`, so the library imports as
`package:{{ package_name }}/{{ package_name }}.dart`.

## Test

```console
$ dart analyze --fatal-infos
$ dart test
```

## License

MIT — see [LICENSE](LICENSE).
