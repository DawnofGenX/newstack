# {{ npm_name }}

A small Redis-protocol (RESP2) key-value server with a hand-written parser. Point
`redis-cli` at it and SET/GET/INCR behave; every reply is produced by
`src/{{ package_name }}/commands.py`, every byte on the wire is parsed by
`src/{{ package_name }}/protocol.py`.

```
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m {{ package_name }} --port 6380
redis-cli -p 6380 ping          # PONG
redis-cli -p 6380 set greeting hi
redis-cli -p 6380 get greeting  # "hi"
```

## Commands

| command | replies |
| --- | --- |
| `PING [message]` | `+PONG`, or the message as a bulk string |
| `ECHO message` | the message as a bulk string |
| `SET key value [EX seconds]` | `+OK`; `EX 0` and `EX abc` are errors |
| `GET key` | the value, or a nil bulk (`$-1`) |
| `DEL key [key ...]` / `EXISTS key [key ...]` | an integer count (duplicates count twice) |
| `INCR key` / `DECR key` | an integer; a value that is not base-10 is an error |
| `DBSIZE`, `FLUSHDB`, `TYPE key`, `TTL key`, `KEYS pattern` | as Redis answers them |
| `COMMAND ...` | an empty array: enough to keep an interactive client quiet |

Everything is in memory: a restart is an empty database. Expiry is lazy — a key
is dropped when it is read after its deadline, and `DBSIZE`/`KEYS` sweep first.

## Traps this starter already paid for

1. **TCP splits commands wherever it likes.** The first version assumed one
   `recv()` was one command; it passed every local test and would fail as soon
   as a command arrived in two packets. `CommandReader` keeps a buffer and only
   consumes a frame once it is complete — the selftest feeds one command one
   byte at a time.
2. **Pipelines are not frames.** Two commands in a single write must produce
   two replies in the same order; a parser that returns a single command per
   read silently drops the second.
3. **Inline and multibulk are two grammars.** `redis-cli` sends `*N` arrays, but
   `redis-cli --pipe`-style tooling and humans send `PING\r\n`. Both are real;
   `*0\r\n` is ignored rather than answered.
4. **Arity errors are errors, not exceptions.** `GET` with no key answers
   `-ERR wrong number of arguments for 'get' command`; the connection stays open.
5. **A malformed frame ends the connection.** After
   `-ERR Protocol error: ...` the server hangs up, exactly like Redis, and the
   reply must be flushed *before* the close.
6. **`INCR` on a non-numeric string is an error and must not overwrite it.** The
   store raises `NotAnInteger` and the value is left alone.
7. **Expiry needs a clock the tests can move.** `Store(clock=...)` is injectable,
   so `TTL`/expiry are checked without sleeping; `TTL` rounds *up* so a key set
   with `EX 10` does not report 9 immediately.
8. **One lock, one keyspace.** Threads per connection plus a single lock is
   plenty here and keeps `INCR` atomic; the selftest fires 100 concurrent
   increments at one key and expects exactly 100.
9. **Shutdown must not wait for an idle client.** The listener is closed and
   every accepted socket is shut down, so the idle client's thread exits; the
   accept loop uses a timeout instead of blocking forever in `accept()`.
