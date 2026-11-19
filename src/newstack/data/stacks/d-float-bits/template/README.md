# {{ project_name }}

Inspect IEEE-754 double-precision bit patterns.

## Usage

```sh
make build
./build/app 1.0
./build/app bits 0x3ff0000000000000
./build/app --help
```

Exit codes: 0 success, 2 usage or parse error.