# {{ title }}

{{ description }}

Bencode is the encoding BitTorrent uses for `.torrent` files and tracker
responses. It has exactly four types — integers, byte strings, lists and
dictionaries — and one property that matters: the encoder is canonical. Keys
are sorted, integers carry no leading zeroes, and a length prefix counts bytes
rather than characters, so an identical value always produces identical bytes
and can be hashed.

## Layout

```
src/Bencode.php    encode(), decode(), and the canonical-form checks
src/Cli.php        argv -> encode | decode, with injected streams
bin/{{ npm_name }} the executable (needs `composer install` for the autoloader)
tests/             PHPUnit: encoding table, round trips, every rejection path
```

## Usage

```console
$ composer install
$ printf '{"a":1,"b":["x"]}' | php bin/{{ npm_name }} encode
d1:ai1e1:bl1:xee
$ printf 'd1:ai1e1:bl1:xee' | php bin/{{ npm_name }} decode
{"a":1,"b":["x"]}
$ php bin/{{ npm_name }} encode torrent.json > out.bencode
```

`encode` reads JSON, `decode` writes JSON, and either takes a path instead of
stdin. Buffers are byte-safe, so binary strings (piece hashes) survive both
directions.

## What decoding rejects

| input | error |
| ----- | ----- |
| `i03e`, `i-0e` | `malformed integer` — no leading zeroes, no negative zero |
| `d1:bi2e1:ai1ee` | `dictionary keys are not in canonical order` |
| `d1:ai1e1:ai2ee` | `duplicate dictionary key` |
| `5:abc` | `string of length 5 ... runs past the end` |
| `li1e` | `unterminated list` |
| `i1ei2e` | `trailing data at offset 3` |
| `x1e` | `unknown type marker` |

Floats are refused on encode: bencode has no float type, and silently rounding
one would change the bytes the other side hashes.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success |
| 1 | invalid JSON or bencode, or an unreadable file |
| 2 | usage error (no command, unknown command, too many paths) |

## Test

```console
$ vendor/bin/phpunit
$ bash smoke.sh
```
