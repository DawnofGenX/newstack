# {{ title }}

A Fortran command-line tool computing mean, median, and stdev of numbers on stdin.

## Build

```
make
```

## Usage

```
./bin/{{ npm_name }} [options]
```

```
$ printf '1 2 3 4\n' | ./bin/{{ npm_name }}
mean:       2.500000
median:     2.500000
stdev:      1.290994
```

Exit codes:

- `0` success
- `1` no input / missing file
- `2` unknown option

## Tests

```
make test
```