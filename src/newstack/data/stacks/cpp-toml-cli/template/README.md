# {{ title }}

A C++17 command-line TOML subset parser that flattens keys.

## Build

```
make
```

## Usage

```
./{{ npm_name }} [FILE...]
```

```
$ printf '[server]\nhost = "localhost"\nport = 8080\n' | ./{{ npm_name }}
server.host = "localhost"
server.port = 8080
```

Exit codes:

- `0` success
- `1` missing or unreadable file
- `2` unknown option

## Tests

```
make test
```