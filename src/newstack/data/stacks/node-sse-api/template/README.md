# {{ project_name }}

{{ description }}

Server-sent events on bare Node: no framework, no dependencies. The HTTP side is
node's `http` module, the stream is text, and the whole suite is `node --test`.

## What is here

| Path | What lives there |
| --- | --- |
| `src/events.js` | the replayable, bounded event log: ids, `since(id)`, trimming |
| `src/frame.js` | SSE framing (`id:` / `event:` / `data:`) and topic validation |
| `src/hub.js` | subscribers, topic fan-out, replay, pruning, heartbeat |
| `src/server.js` | three routes: `/health`, `/events`, `/publish` |
| `src/main.js` | PORT/HOST/SSE_HEARTBEAT_MS, listen, SIGTERM drain |
| `tools/contract.mjs` | the live contract: a real stream, a real reconnect, a heartbeat |
| `tests/*.test.js` | `node --test` suite, including a live server on port 0 |

## Run it

```bash
npm install          # nothing to install; keeps the habit
node src/main.js     # http://127.0.0.1:8080
npm test
```

Watch a stream in one terminal:

```bash
curl -N http://127.0.0.1:8080/events
```

Publish from another:

```bash
curl -s -X POST http://127.0.0.1:8080/publish \
  -H 'content-type: application/json' \
  -d '{"topic":"metrics","data":{"users":3}}'
# {"id":1,"subscribers":1}
```

The subscriber prints:

```
id: 1
event: metrics
data: {"users":3}
```

Reconnect with `Last-Event-ID` (browsers send it automatically on an
`EventSource` retry) and the events you missed are replayed:

```bash
curl -N -H 'Last-Event-ID: 4' http://127.0.0.1:8080/events
curl -N 'http://127.0.0.1:8080/events?last_id=4'   # same thing for curl
```

`/events?topic=metrics` subscribes to one topic; no `topic` means everything.

## Traps this starter already paid for

- **`res.write()` after the client leaves.** The write does not throw, it just
  goes nowhere, so the subscriber set grows all afternoon. Every write checks
  `writableEnded`/`destroyed` and prunes, and `/events` also removes the slot on
  the response's `close` event.
- **A newline in `data:` splits one event into two.** The payload is
  JSON-encoded, so a multi-line string is `"one\ntwo"` on one line. Writing
  `String(data)` produces two `data:` lines and a client that sees garbage.
- **A newline in the *event name* is a frame injection.** The topic becomes the
  `event:` header, so topics are validated against `[A-Za-z0-9][A-Za-z0-9._-]*`
  before a stream opens.
- **Node buffers the response until you flush the headers.** Without
  `Content-Type: text/event-stream` plus `flushHeaders()`, the first event sits
  in a buffer and the client waits for it.
- **A proxy will happily buffer the stream.** `X-Accel-Buffering: no` (nginx)
  and `Cache-Control: no-transform` are written by default; without them the
  stream arrives as one response when it ends, which is not a stream.
- **A silent stream gets closed by something in the middle.** Comment lines
  (`: ping`) keep it alive without inventing events; `SSE_HEARTBEAT_MS` sets the
  cadence (`0` disables it).
- **`server.close()` waits for open streams forever.** Those connections are
  deliberately not closing. The shutdown path closes the hub, then
  `closeAllConnections()`, with a 2 s backstop.
- **`npm test` hangs if a timer is left referenced.** The heartbeat interval is
  `unref()`ed, so the suite exits when the last assertion does.
