# {{ title }}

{{ description }}

Requires Go 1.24 or newer.

## Run

```bash
go run .
curl -sS http://127.0.0.1:5543/metrics
```

## Check

```bash
go vet ./...
go test ./...
go build -o bin/server .
bash smoke.sh
```

## Traps this starter already paid for

- Metrics are registered on the default Prometheus registry.
- /metrics is served via promhttp.Handler.
- A counter and histogram are updated for every request.
- PORT env var overrides the default 5543.
