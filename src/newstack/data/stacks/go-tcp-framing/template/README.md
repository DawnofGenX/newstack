# a length-prefixed TCP service

Not HTTP: every message on the wire is a 4-byte big-endian length followed by
that many bytes of JSON. One request frame in, one reply frame out, in order,
for as long as the connection lives.

```
go build -o build/{{ npm_name }} .
./build/{{ npm_name }}            # 127.0.0.1:5481, PORT/HOST to override
go test ./...
./build/{{ npm_name }} --selftest
```

| frame | meaning |
| --- | --- |
| `{"op":"ping"}` | `{"ok":true,"pong":true}` |
| `{"op":"count","text":"a b\nc\n"}` | `{"ok":true,"lines":2,"words":3,"bytes":6}` |
| `{"op":"count"}` | `{"ok":false,"error":"missing_text",…}` |
| anything else | `invalid_json`, `missing_op`, `unknown_op` |

A protocol mistake is still a reply: the connection stays open, because a
client that gets a frame back can recover.

## Traps this starter already paid for

1. **The length prefix is an allocation instruction from the network.** A
   4-byte header saying 4 GiB is one packet away, so the cap is checked before
   a buffer is allocated for it (`ErrFrameTooLarge`), and the connection is
   closed afterwards because the stream is no longer frame-aligned.
2. **Zero-length frames are a framing mistake, not an empty message.** `size
   == 0` is refused rather than answered, otherwise a closed writer and an
   empty payload look the same.
3. **A body shorter than its header is not a message.** `io.ReadFull` turns a
   truncated frame into an error, where a bare `Read` would silently return
   half a payload.
4. **Write the header and the body in one `Write`.** Two writes mean a slow
   reader can see a header without a body and time out in the middle of a
   message that was never wrong.
5. **JSON has no `\x` escape.** A test payload written `"a\tb\x0bc"` is
   `invalid_json` at the server -- use `\u000b`/`\u000c`, or the failure looks
   like a counting bug.
6. **A zero count must be printed, not omitted.** `omitempty` on an `int` drops
   `"lines":0`, and a client cannot tell "no lines" from "no field"; the reply
   struct uses pointers for exactly that reason.
7. **Shutdown must close the connections, not just the listener.** A client
   parked in a read keeps the process alive; `Shutdown` closes every tracked
   connection and waits with a deadline.
8. **An idle deadline is a resource bound.** Without `SetReadDeadline`, half a
   million half-open connections accumulate a goroutine each.
9. **One goroutine per connection, no shared state.** The counters live in the
   handler, so two clients cannot interleave their numbers.
