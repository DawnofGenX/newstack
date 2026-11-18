# {{ title }}

{{ description }}

Requires Go 1.24 or newer.

## Run

```bash
go run .
curl -sS http://127.0.0.1:5540/health
```

## Check

```bash
go vet ./...
go test ./...
go build -o bin/server .
bash smoke.sh
```

## Traps this starter already paid for

- Token bucket is per client IP (RemoteAddr).
- 429 responses include a Retry-After header.
- The limiter is in-memory and per-process.
- PORT env var overrides the default 5540.
