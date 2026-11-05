# {{ title }}

A gRPC service in Go generated from a protobuf contract. The `.proto` file is the source of
truth: the generated stubs are not committed, `buf generate` recreates them.

## Requirements

- Go 1.24 or newer
- [buf](https://buf.build/docs/installation) and the two protoc plugins:

```sh
go install github.com/bufbuild/buf/cmd/buf@v1.61.0
go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.10
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.6.1
export PATH="$(go env GOPATH)/bin:$PATH"
```

## Layout

```
proto/textstat/v1/textstat.proto   the contract
buf.yaml, buf.gen.yaml             lint rules and codegen plugins
gen/                               generated stubs (gitignored, recreated by buf generate)
internal/textstat/count.go         line/word/byte counting, no gRPC in sight
internal/server/server.go          the RPC handler; translates errors to status codes
cmd/{{ npm_name }}/main.go           the server: health service, reflection, graceful shutdown
cmd/probe/main.go                  a tiny client used by the smoke test and by you
```

Counting rules match `wc`: a line is a `\n`, a word is a maximal run of non-space characters,
bytes are UTF-8 bytes (`héllo` is 5 characters and 6 bytes).

## Run it

```sh
buf generate
go run ./cmd/{{ npm_name }}            # listens on 127.0.0.1:50051, or set PORT/ADDR
go run ./cmd/probe -text 'a b\nc\n'   # lines=2 words=3 bytes=6
```

`-text` accepts the escape sequences a shell single-quoted argument carries, so `\n` is a real
newline rather than a literal backslash-n.

Because the server registers reflection, `grpcurl` works with no local copy of the `.proto`:

```sh
grpcurl -plaintext -d '{"text":"hello world\n"}' 127.0.0.1:50051 textstat.v1.TextStatService/Count
```

## Test it

```sh
go test ./...
```

Two kinds of test are included and they catch different failures:

- `internal/textstat` is a plain table test over the counting logic.
- `internal/server` drives the handler over [bufconn](https://pkg.go.dev/google.golang.org/grpc/test/bufconn),
  an in-memory listener that still runs the real gRPC stack (marshalling, status codes), plus
  one test that dials a real TCP socket so listener setup is not the only thing untested.

## Notes

- `go.mod` pins gRPC rather than floating on the newest release: newer gRPC versions raise the
  `go` directive, which would silently drop older toolchains. Bump both together.
- `buf.yaml` enables the STANDARD lint rules, which require a service name ending in `Service` —
  that is why the service is `TextStatService`, not `TextStat`.
- Invalid UTF-8 in a string field is rejected by protobuf marshalling on the client, before the
  handler runs; the handler's own guard still returns `InvalidArgument` for in-process callers.
