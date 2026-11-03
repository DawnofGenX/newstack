# {{ title }}

{{ description }}

A small Perl 5 command line tool with no CPAN dependencies outside core:
counting lives in `Textstat::Counts` so `Test::More` drives it directly,
`Textstat::Options` turns `@ARGV` into a decision without printing or exiting,
and `bin/{{ npm_name }}` is the only place that reads files, prints and calls
`exit`.

## Layout

```
Makefile.PL                     ExtUtils::MakeMaker build script (NAME, EXE_FILES, tests)
bin/{{ npm_name }}              executable entry point, shebang #!/usr/bin/env perl
lib/Textstat.pm                 thin facade: version and count_text()
lib/Textstat/Counts.pm          line / word / byte value object plus pure counting
lib/Textstat/Options.pm         argv parsing and help text, never exits
t/01-counts.t                   tests for counting
t/02-options.t                  tests for parsing
t/03-cli.t                      runs the real script and asserts exit codes 0/1/2
```

Every module starts with `use strict; use warnings;`, and the build needs only
`ExtUtils::MakeMaker` and `Test::More`, both shipped with perl.

## Build

```console
$ perl Makefile.PL
$ make
```

## Run

```console
$ perl bin/{{ npm_name }} --help
$ perl bin/{{ npm_name }} README.md
$ printf 'one two\nthree\n' | perl bin/{{ npm_name }} -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ make test
```

`t/03-cli.t` shells out to `bin/{{ npm_name }}` with `system`, so the exit
codes are proven by the real binary rather than by calling a function.

## Rename

The distribution name and module namespace are `Textstat`. To rename:

1. change `NAME` in `Makefile.PL` and `our $VERSION` stays in `lib/Textstat.pm`;
2. rename `lib/Textstat.pm`, `lib/Textstat/`, and the `package` lines in each
   module (directories must match the namespace case exactly on Linux);
3. rename `bin/{{ npm_name }}` if you want a different command name and update
   `EXE_FILES`.

## License

MIT — see [LICENSE](LICENSE).
