# {{ title }}

A C command-line hex dump tool.

## Build

```
make
```

## Usage

```
./build/{{ npm_name }} [FILE...]
```

Reads each FILE (or stdin when none) and prints a hexadecimal dump with
byte offsets and an ASCII gutter.

```
$ printf 'Hello\n' | ./build/{{ npm_name }}
00000000  48 65 6c 6c 6f 0a           |Hello.|
```

Exit codes:

- `0` success
- `1` missing or unreadable file
- `2` unknown option

## Tests

```
make test
```