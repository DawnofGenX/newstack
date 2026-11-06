# {{ title }}

Signed requests over a canonical form, so a copy does not break a signature.

{{ description }}

## The rules this project keeps

1. **A signature covers the canonical form, not the bytes on the wire.** `%7E`
   and `~` are the same character, so both are decoded and re-encoded in
   uppercase; a path segment is canonicalised on its own, so an escaped `%2F`
   stays data instead of becoming a new separator.
2. **Two spellings of one query are one query.** Parameters are sorted by
   encoded name and then encoded value, duplicates are kept, and an empty field
   is dropped. Reordering a request therefore does not invalidate it.
3. **A plus sign is a plus sign.** Form encoding writes a space as `+`, which
   belongs to a different grammar; here `+` decodes to `+` and `%2B` also
   decodes to `+`, while a space is only ever `%20`.
4. **The signing string is one fact per line.** Algorithm, timestamp, method,
   canonical target, body hash, then each signed header as `name:value`. A
   separator that can appear inside a field is a separator that can be forged, so
   there is no separator: header whitespace is collapsed and the newline is the
   boundary.
5. **The body is covered by its hash.** The hash of no body is still a hash,
   so an empty body is signed like any other and a changed amount is refused.
6. **A signature has a lifetime and a nonce.** Verification compares the current
   time against an integer expiry, tolerates a small clock skew, and remembers
   which signatures it has accepted: the second use of a token is refused with
   the time of the first.
7. **A header outside the signed set was never covered.** Sign what you trust;
   story 5 shows a signature that still verifies after `content-type` was
   rewritten, then the same signature with that header included, refusing.

Every refusal names the rule that failed: `expired 1 s ago`,
`the signature does not match this request`,
`this signature was already accepted at 1780000000`,
`issued 600 s in the future, past the 60 s skew allowance`.

## Try it

```console
$ {{ npm_name }} demo
1. reordering the query does not invalidate the signature
  signed url      /items?b=2&a=1
  sent url        /items?a=1&b=2
  canonical       /items?a=1&b=2 and /items?a=1&b=2
  verdict         ok       accepted, 300 s of life left
  a signature over the raw url would compare a6b3a2e53f14… with 66956e3dc4df…
  and those differ, which is why the naive version fails on a copy
  -> holds

4. expiry is arithmetic
  issued          1780000000 (300 s)
  expires         1780000300
  exactly on time ok       accepted, 0 s of life left
  one second late refused  expired 1 s ago
  expiry is an integer comparison, not a guess about latency
  -> holds
```

The signing string for

```console
$ {{ npm_name }} sign --url "/a?b=2&a=1" --secret dev-secret \
    --timestamp 1780000000 --signed-header x-user --header "X-User: alice" --show-string
```

is this, in order:

```console
request      signed
signing string
  hmac-sha256
  1780000000
  GET
  /a?a=1&b=2
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  x-user:alice
algorithm    hmac-sha256
timestamp    1780000000
expires      1780000300 (300 s of life)
target       /a?a=1&b=2
headers      x-user
signature    f94c97ab2ecdbebc96897d57af1a6933f5e2e917d9d0879a1141e36b187b9a8c
```

The body hash is the SHA-256 of nothing, because `--body` was not given. Sign a
body to change that line.

Verifying is a two-line answer:

```console
$ {{ npm_name }} verify --url "/a" --secret dev-secret --now 1780000000 --signature-file sig.json
ok       accepted, 300 s of life left
$ {{ npm_name }} verify --url "/b" --secret dev-secret --now 1780000000 --signature-file sig.json
refused  the signature does not match this request
```

## The commands

| Command | What it answers |
| --- | --- |
| `sign --url PATH [--method GET]` | The signature, its expiry and the canonical target |
| `string --url PATH` | Only the signing string, line by line |
| `verify --url PATH` | Whether this request may be served, and why not |
| `demo` | The six stories above, each computed |
| `selftest` | The same rules checked in-process |

`sign --json` writes the object `verify --signature-file` reads. Timestamps are
epoch seconds; `--timestamp` and `--now` default to the current time, so a test
that wants a fixed answer should pass both.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | The request was signed, or the signature was accepted, or the demo held |
| `1` | The signature was refused, or a demo story no longer holds |
| `2` | The arguments or the request cannot be used: a missing `--url`, a host in the URL, a bad header line, an unknown JSON file |

A refusal is a data-quality signal, so `verify` returns `1` rather than `2`: the
caller asked a question and got an answer.

## Layout

| Path | What lives there |
| --- | --- |
| `src/{{ package_name }}/canonical.py` | Escaping, path segments, query ordering |
| `src/{{ package_name }}/sign.py` | The signing string, signing, verification, nonces |
| `src/{{ package_name }}/demo.py` | The six computed stories |
| `src/{{ package_name }}/cli.py` | Argument parsing and exit codes |

## What this project does not do

It does not sign the query as an opaque string (that is the bug it exists to
avoid), it does not support HMAC algorithms other than SHA-256, it does not store
nonces in a shared store (use a Redis `SETNX` if more than one verifier exists),
and it does not implement AWS Signature Version 4, whose canonicalisation rules
differ in detail from these.

## Development

```console
$ uv venv && uv pip install -e . pytest ruff
$ .venv/bin/python -m pytest
$ .venv/bin/python -m {{ package_name }} selftest
$ PY=.venv/bin/python bash smoke.sh
```

Licensed under {{ license }}.
