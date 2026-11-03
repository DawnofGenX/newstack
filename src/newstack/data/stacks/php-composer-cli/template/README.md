# {{ title }}

{{ description }}

A small PHP 8.3 command line tool: counting lives in a pure class (`TextStat`)
so tests drive it directly, and `Cli` is a thin entry point that owns printing
and exit codes. Composer handles PSR-4 autoloading and PHPUnit runs the suite.

## Layout

```
composer.json                      PHP ^8.3, PSR-4 autoloading, PHPUnit 11
phpunit.xml                        test suite configuration
bin/{{ npm_name }}                 executable entry point with a php shebang
src/Counts.php                     line / word / byte value object
src/TextStat.php                   pure counting, no I/O
src/Options.php                    hand-rolled argv parsing and help text
src/Options/Mode.php               enum: ALL, LINES, WORDS, BYTES
src/Options/Status.php             enum: OK, HELP, VERSION, ERROR
src/Cli.php                        reads files or stdin, prints, returns an exit code
tests/                             PHPUnit 11 tests for counting, parsing and exit codes
```

No runtime dependencies: argument parsing is hand-rolled and PHPUnit is the
only development dependency.

## Build

```console
$ composer install
```

The first install writes `composer.lock`; commit it so later installs resolve
the same versions.

## Run

```console
$ php bin/{{ npm_name }} --help
$ php bin/{{ npm_name }} README.md
$ printf 'one two\nthree\n' | php bin/{{ npm_name }} -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ vendor/bin/phpunit
```

## License

MIT — see [LICENSE](LICENSE).
