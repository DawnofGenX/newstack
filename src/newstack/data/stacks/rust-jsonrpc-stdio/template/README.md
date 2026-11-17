# {{ npm_name }}

{{ description }}

One JSON request per line on stdin, at most one JSON response per line on stdout.
That is the whole transport, and it is the transport editors use to talk to
language servers all day.

```bash
cargo run
```

Then paste a request and press enter:

```json
{"jsonrpc":"2.0","id":1,"method":"add","params":{"a":2,"b":3}}
```

```json
{"jsonrpc":"2.0","id":1,"result":{"sum":5}}
```

Piping a whole session at it works too, which is how the smoke test drives it:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"add","params":{"a":2,"b":3}}' \
  '{"jsonrpc":"2.0","id":2,"method":"notes.list"}' \
  | cargo run --quiet
```

## The methods

| method | params | result |
| --- | --- | --- |
| `add` | `{"a":<int>,"b":<int>}` | `{"sum":<int>}` |
| `echo` | anything | the params, unchanged |
| `notes.put` | `{"title":"…","body":"…"}` | `{"stored":<count>}` |
| `notes.list` | none | `{"notes":[{"title","body"},…],"count":<n>}` |
| `notes.drop` | `{"title":"…"}` | `{"removed":<bool>}` |

Notes live in memory for the length of the session, so a client can restart the
process to start from nothing.

## The error codes

`-32700` parse error, `-32600` invalid request, `-32601` method not found,
`-32602` invalid params. They are the reserved spec codes, not invented ones:
clients already branch on them. `invalid params` errors carry the offending
params back in the optional `data` field, because "bad params" without the
params is a support ticket.

## What the smoke test proves

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release
bash smoke.sh
```

`smoke.sh` pipes six lines at the release binary and asserts five answers: the
sum, the state the silent notification changed, the three error codes, and that
stderr stayed out of the response stream.

## Traps this starter already paid for

- **Flush after every response.** The client is blocked on the line it asked
  for. A response sitting in a buffer is a hung client, not a fast one.
- **A notification is a request without an `id`.** It is executed and it is
  never answered — not with a result, not with an error, not with `null`.
- **An empty batch is not an empty answer.** `[]` is one `-32600` error object;
  answering `[]` tells the client nothing happened, which is wrong.
- **An explicit `"id": null` is not an answer slot.** Serde cannot tell it from
  a missing `id` here, so it is treated as a notification: executed, unanswered.
  Judge "was this a notification" by absence, never by a null id.
- **Batches answer with one array, in request order.** Not one line per request.
- **Diagnostics go to stderr.** Anything on stdout that is not a response
  breaks the framing for every client.
- **Closing stdin ends the session cleanly.** A CI job that writes requests and
  never closes stdin hangs until the job timeout kills it.
