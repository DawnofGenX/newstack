# {{ title }}

{{ description }}

A Perl INI reader with no dependencies beyond core: parsing lives in
`lib/IniLite/Parse.pm` (pure, no I/O), argv parsing in
`lib/IniLite/Options.pm`, and `bin/{{ npm_name }}` is the thin entry point that
owns output and exit codes.

## Usage

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} app.ini
$ ./bin/{{ npm_name }} -s server app.ini
$ ./bin/{{ npm_name }} -g server.host app.ini
$ ./bin/{{ npm_name }} --list-sections app.ini
$ ./bin/{{ npm_name }} --json app.ini
$ cat app.ini | ./bin/{{ npm_name }} -g port
```

Options:

| flag | meaning |
| ---- | ------- |
| `-s, --section NAME` | print only the named section |
| `-g, --get PATH` | print one value: `section.key`, or `key` in the unnamed section |
| `--json` | emit the whole document as a JSON object |
| `--list-sections` | print section names, one per line |
| `-h, --help` | show help and exit 0 |
| `-V, --version` | show the version and exit 0 |

## INI semantics

* `key = value` and `key: value` are both accepted; the value keeps any further
  `=` or `:`.
* `[section]` starts a section; keys before the first header belong to the
  unnamed section, whose keys are addressable bare (`-g port`).
* `;` and `#` start a comment at the beginning of a line, or after whitespace,
  so `pass#1` survives while `pass   # note` loses the note.
* Matching single or double quotes are stripped, and `\n`, `\t` and `\\x` are
  resolved inside a quoted value.
* Section order and key order are preserved, because rewriting an INI file in a
  different order is a diff nobody asked for.
* A line that is neither a header nor a pair stops the read with
  `error: line N: expected [section] or key = value`.

## Layout

```
bin/{{ npm_name }}             entry point: argv -> help | usage | output
lib/IniLite.pm                  facade: IniLite->parse_text($text)
lib/IniLite/Parse.pm            parse(), get(), pairs(), lookup(), flatten()
lib/IniLite/Options.pm          parse(): argv -> options hashref
t/01-parse.t                    sections, comments, quotes, duplicates, errors
t/02-options.t                  every parser branch
t/03-cli.t                      the real binary: stdout and exit codes
Makefile.PL                     ExtUtils::MakeMaker distribution
```

## Requirements

Perl 5.10 or newer with `ExtUtils::MakeMaker` and `make`; `JSON::PP` is core
since 5.14 and is the only module used for `--json`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` and `--version` |
| 1 | the input could not be read, or it is not valid INI |
| 2 | usage error: unknown flag, unknown section, unknown key, missing value |

## Test

```console
$ perl Makefile.PL && make test
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.
