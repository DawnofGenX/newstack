# {{ title }}

{{ description }}

An append-only hash chain, the structure behind tamper-evident audit logs: each
entry commits to the digest of the entry before it, so editing, deleting,
reordering or truncating history is detectable by anyone holding the file —
without a central authority and without storing anything secret.

## Layout

```
lib/hash_chain.rb        canonical(): sorted-key JSON; link(): the sha256 of one entry; Chain: append + verify!
lib/hash_chain/cli.rb    argv -> append | verify | head | show | list, with injected stdio and clock
bin/{{ npm_name }}       the executable
test/                    minitest: digest determinism, tamper shapes, CLI exit codes
```

Standard library only: `digest`, `json`, `optparse`.

## Usage

```console
$ bin/{{ npm_name }} append '{"event":"created","amount":10}' --file chain.ndjson
9f2c...64 hex characters
$ bin/{{ npm_name }} append '{"event":"paid"}' --file chain.ndjson
4a71...64 hex characters
$ bin/{{ npm_name }} verify --file chain.ndjson
ok 2 entries
$ bin/{{ npm_name }} head --file chain.ndjson
4a71...64 hex characters
```

`--at EPOCH` pins the timestamp so runs are reproducible; without it the clock
supplies the value.

Each entry's digest is sha256 over four lines — sequence number, timestamp,
previous digest, canonical payload — so no field can be smuggled into its
neighbour by moving a newline. Payload keys are sorted before hashing, so two
processes that build the same object in a different order agree.

Editing history breaks verification at the first bad entry:

```console
$ bin/{{ npm_name }} verify --file chain.ndjson
broken entry 1: digest does not match contents
```

The same check catches a dropped entry (`sequence is 2, expected 1`) and a
reordered pair.

## Commands

| command | output | exit |
| ------- | ------ | ---- |
| `append PAYLOAD` | the new digest | 0 ok, 1 payload is not JSON or the file is unwritable |
| `verify` | `ok N entries`, or `broken entry K: reason` on stderr | 0 clean, 1 broken |
| `head` | digest of the last entry | 0 ok, 1 empty chain |
| `show [INDEX]` | one entry as JSON, default the last | 0 ok, 1 missing |
| `list` | `INDEX DIGEST` per entry | 0 |

A usage error (unknown flag or command, missing payload) exits 2 and prints the
usage text on stderr.

## Test

```console
$ rake test
```
