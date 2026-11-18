# {{ title }}

{{ description }}

Requires Go 1.24 or newer.

## Run

```bash
UPSTREAM=http://127.0.0.1:5542 go run .
curl -sS http://127.0.0.1:5541/health
```

## Check

```bash
go vet ./...
go test ./...
go build -o bin/server .
bash smoke.sh
```

## Traps this starter already paid for

- Hop-by-hop headers are stripped on both request and response.
- X-Forwarded-For is appended, not overwritten.
- Upstream URL comes from the UPSTREAM env var (default 127.0.0.1:5542).
- PORT env var overrides the default 5541.
