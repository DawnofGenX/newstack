# {{ project_name }}

Percent-encode and decode strings per RFC 3986.

## Usage

```sh
make
./build/{{ npm_name }} encode "a b"
./build/{{ npm_name }} decode "a%20b"
./build/{{ npm_name }} --help
```

Exit codes: 0 success, 2 usage or parse error.