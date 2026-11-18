# {{ title }}

{{ description }}

Base58 is base58 because it drops the four characters that look alike in print —
`0`, `O`, `I` and `l` — so a value can be read off a screen or a printout without
guessing. The arithmetic is an ordinary base conversion on a big integer; the
careful parts are leading zero bytes and the optional checksum.

## Layout

```
lib/base58.rb           encode, decode, checksum, encode_check, decode_check
lib/base58/cli.rb       the command line, with stdin/stdout/stderr injected
bin/                    the executable
test/                   minitest: reference vectors, round trips, CLI exit codes
```

## Usage

```console
$ bin/{{ npm_name }} encode 68656c6c6f20776f726c64
StV1DL6CwTryKyV
$ bin/{{ npm_name }} decode 2g
61
$ bin/{{ npm_name }} --text encode hello
Cn8eVZg
$ bin/{{ npm_name }} check-encode 000f9a4b120000000000
12JNo32w2yrmQuWFckG
$ bin/{{ npm_name }} check-decode 12JNo32w2yrmQuWFckG
000f9a4b120000000000
```

Values are read as hex unless `--text` is given. With no value on the command
line the value is read from standard input, which makes the tool work inside a
pipe:

```console
$ printf 'hello world' | bin/{{ npm_name }} --text encode
StV1DL6CwTryKyV
```

## Leading zeros

Each leading zero byte becomes a leading `1`:

```console
$ bin/{{ npm_name }} encode 000001
112
```

That is what makes the encoding reversible: the number itself has no leading
zeros, so the `1`s are the only place that information can live.

## Base58Check

`check-encode` appends four bytes — the first four bytes of SHA-256 applied
twice — and `check-decode` verifies them, so one mistyped character is refused
instead of decoding to plausible-looking nonsense:

```console
$ bin/{{ npm_name }} check-decode 12JNo32w2yrmQuWFckH
error: checksum mismatch
$ echo $?
1
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` |
| 1 | bad input: a character outside the alphabet, odd or non-hex input, a bad checksum |
| 2 | usage error: no command, an unknown command, an extra argument, no value |

## Test

```console
$ rake test
$ bash smoke.sh
```
