# groovy-ini-cli

INI reader with typed values and `--get`.

## Usage

```
./bin/groovy-ini-cli --help
./bin/groovy-ini-cli --get app.count sample.ini
./bin/groovy-ini-cli sample.ini
```

Exit codes: `0` success, `1` missing file or key, `2` usage error.
