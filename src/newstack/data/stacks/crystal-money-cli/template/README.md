# {{ title }}

{{ description }}

Money arithmetic in integer minor units — no floats, so `USD 0.1 + USD 0.2`
is exactly `USD 0.30`. Splitting an amount across ratios always adds back up to
the original, down to the last cent.

## Usage

```sh
./bin/{{ package_name }} add 'USD 1.50' 'USD 2.25'    # USD 3.75
./bin/{{ package_name }} sub 'USD 10.00' 'USD 0.25'   # USD 9.75
./bin/{{ package_name }} scale 'USD 1.05' 3           # USD 3.15
./bin/{{ package_name }} split 'USD 10.00' 1 2        # USD 3.34 USD 6.66
./bin/{{ package_name }} show 'USD 12.34'             # $12.34
printf 'USD 1.00\nUSD 0.50\n' | ./bin/{{ package_name }} sum
```

Amounts are written `CODE 12.34`: a three-letter currency, one space, then at
most two decimal places. Thousands separators are accepted.
Exit codes: `0` success, `1` bad amount or input, `2` usage.

## Layout

- `src/money/amount.cr` — parsing, arithmetic, allocation, formatting.
- `src/money/cli.cr` — the command set; every I/O device is a parameter.
- `src/money.cr` — the facade and the only `exit`.
- `spec/` — amount and CLI specs, including the allocation invariant.

## Tests

```sh
crystal spec
mkdir -p bin && crystal build -o bin/{{ package_name }} src/money.cr
```

There are no shard dependencies, so `shards install` is never needed.
