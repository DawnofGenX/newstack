# {{ title }}

{{ description }}

A stdlib-only Go HTTP service: `net/http` routing, JSON endpoints, an in-memory
store, table tests with `httptest`, and graceful shutdown on SIGINT/SIGTERM.
No third-party dependencies.

## Requirements

- Go 1.24 or newer

## Run

```sh
go run .
```

Listens on port 8080 by default. Pick another port with `PORT`:

```sh
PORT=9000 go run .
```

## Endpoints

| Method | Path      | Description                       |
| ------ | --------- | --------------------------------- |
| GET    | `/health` | Liveness probe                    |
| GET    | `/items`  | List stored items                 |
| POST   | `/items`  | Create an item from `{"name":"…"}`|

```sh
curl localhost:8080/health
curl localhost:8080/items
curl -X POST -H 'content-type: application/json' -d '{"name":"probe"}' localhost:8080/items
```

The service shuts down gracefully when it receives SIGINT or SIGTERM, giving
in-flight requests up to 5 seconds to finish.

## Test

```sh
go test ./...
```

## Build

```sh
go build -o bin/server .
./bin/server
```

## Layout

```
main.go                     entry point: env, http.Server, graceful shutdown
internal/api/api.go         handler, routes, in-memory store
internal/api/api_test.go    table-driven httptest suite
```

## License

MIT - see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.
