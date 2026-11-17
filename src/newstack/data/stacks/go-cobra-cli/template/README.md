# {{ npm_name }}

A Cobra-based Go CLI with subcommands, tests, and a smoke run of the binary.

```bash
go test ./...
go build -o {{ npm_name }} .
./{{ npm_name }} --help
bash smoke.sh
```
