# {{ title }}

{{ description }}

## Usage

```sh
go test ./...
go build -o bin/{{ npm_name }} .
./bin/{{ npm_name }} -salt 00010203 -info context -length 32 0b0b0b0b
printf 'key material' | ./bin/{{ npm_name }} -length 16
```

HKDF-SHA256 as specified by RFC 5869: `-salt` takes hex, `-info` takes text and
`-length` defaults to 32 bytes (the maximum is 8160). The RFC 5869 test vectors
are part of the test suite.
