# {{ title }}

{{ description }}

## Requirements

- Go 1.24 or newer

## Usage

```sh
go run . greet --name you
```

Output:

```
Hello, you!
```

Print the version:

```sh
go run . --version
```

## Development

```sh
go test ./...
```

Build a binary:

```sh
go build -o bin/{{ npm_name }} .
```

Run the built binary:

```sh
./bin/{{ npm_name }} greet --name you
```

## Layout

```
main.go                     entry point, delegates to internal/app
internal/app/app.go         command logic, testable without a binary
internal/app/app_test.go    table tests
```

## License

MIT - see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.
