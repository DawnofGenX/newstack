# {{ title }}

{{ description }}

## Usage

```sh
./bin/{{ npm_name }} README.md
./bin/{{ npm_name }} --algo sha1 README.md
./bin/{{ npm_name }} --algo crc32 README.md
./bin/{{ npm_name }} README.md > SUMS && ./bin/{{ npm_name }} --check SUMS
printf 'hello' | ./bin/{{ npm_name }} -
```

Output is `sha256sum`-compatible: `<hex>  <path>`. `--check` reads the same format back and prints
`<name>: OK` or `<name>: FAILED expected != actual` per line, then a summary. A digest shorter than
the computed one is accepted as a prefix, which makes truncated checksum files usable.

Exit codes: 0 success, 1 a file could not be read or a checksum did not match, 2 usage error.

## Algorithms

`sha256` (default), `sha1`, `md5` and `crc32` (IEEE 802.3, the zip/`cksum` polynomial). CRC32 is
implemented here with a precomputed table, so nothing depends on a particular runtime build.

## Test

```sh
bun test
```
