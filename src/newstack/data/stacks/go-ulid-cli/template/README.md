# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/app .
./bin/app -gen -n 5
./bin/app -gen -at 2023-11-14T22:13:20Z
./bin/app -parse 01HF7YAT31JZHSMW1CG9RHD3S1
```

ULIDs are 26 characters of Crockford base32: a 48 bit millisecond timestamp
followed by 80 bits of entropy, so lexicographic order matches creation time.
