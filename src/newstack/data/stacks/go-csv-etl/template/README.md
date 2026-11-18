# {{ title }}

{{ description }}

Requires Go 1.24 or newer.

## Run

```bash
go run . -in data/input.csv
```

## Check

```bash
go vet ./...
go test ./...
go build -o bin/etl .
bash smoke.sh
```

## Traps this starter already paid for

- CSV header must be `id,email,amount`.
- Duplicate ids are dropped (first wins).
- Invalid rows are counted but do not abort the run.
- Output is compact JSON on stdout.
