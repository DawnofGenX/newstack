# {{ title }}

{{ description }}

UUIDv7 (RFC 9562) puts a 48-bit millisecond timestamp in front of 74 random bits,
so the identifiers sort by creation time as plain text — ideal for database keys
you want to paginate in insertion order — while staying unguessable. This tool
generates them, takes them apart, and orders a stream of them.

## Layout

```
src/uuid/format.ts   uuidV7(): the bit layout; parse(): version, variant, timestamp; compare()
src/cli.ts           gen | parse | sort | validate, with injected io
bin/{{ npm_name }}   the executable
tests/               bun test: bit layout, timestamp round trip, CLI exit codes
```

No dependencies: `node:crypto` supplies the random bytes.

## Usage

```console
$ ./bin/{{ npm_name }} gen
018bcfe5-6800-7a3c-9f21-4d0b8e6a5c72
$ ./bin/{{ npm_name }} gen --count 3
018bcfe5-6801-7...
018bcfe5-6801-7...
018bcfe5-6801-7...
$ ./bin/{{ npm_name }} parse 018bcfe5-6800-7a3c-9f21-4d0b8e6a5c72
uuid=018bcfe5-6800-7a3c-9f21-4d0b8e6a5c72
version=7
variant=rfc4122=true
timestamp_ms=1700000000000
timestamp_iso=2023-11-14T22:13:20.000Z
$ printf '%s\n%s\n' "$later" "$earlier" | ./bin/{{ npm_name }} sort
$ ./bin/{{ npm_name }} validate 5b1e6f9a-2f7c-4b6d-9c1e-0d5f2b8a7c31
5b1e6f9a-2f7c-4b6d-9c1e-0d5f2b8a7c31
```

## The bit layout

| bytes | bits | contents |
| ----- | ---- | -------- |
| 0-5 | 48 | Unix milliseconds, big-endian |
| 6 | 4 + 4 | version `0111`, then 4 random bits |
| 7 | 8 | random |
| 8 | 2 + 6 | variant `10`, then 6 random bits |
| 9-15 | 56 | random |

`parse` also accepts v4 and v1 uuids; it reports `version` and the variant, and
only v7 uuids have a `timestamp_ms`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` |
| 1 | invalid uuid, or a stdin line that is not a uuid |
| 2 | usage error (unknown command, bad `--count`, missing argument) |

## Test

```console
$ bun test
$ bash smoke.sh
```
