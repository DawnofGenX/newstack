# {{ title }}

{{ description }}

SemVer 2.0.0 parsing, validation, comparison and sorting from the command line,
with no runtime dependencies beyond Ruby.

## Layout

```
lib/semver.rb           parse, valid?, compare, bump
lib/semver/cli.rb       the command line, with stdin/stdout/stderr injected
bin/                    the executable
test/                   minitest: precedence tables, CLI exit codes
```

## Usage

```console
$ bin/{{ npm_name }} compare 1.0.0 2.0.0
-1
$ bin/{{ npm_name }} validate 1.2.3-rc.1
valid
$ bin/{{ npm_name }} sort 2.0.0 1.0.0 1.5.0
1.0.0
1.5.0
2.0.0
$ bin/{{ npm_name }} bump 1.2.3 minor
1.3.0
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` |
| 1 | bad input: an invalid version string |
| 2 | usage error: no command, unknown command, wrong arity |

## Test

```console
$ rake test
$ bash smoke.sh
```