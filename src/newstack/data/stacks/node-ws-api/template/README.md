# {{ project_name }}

{{ description }}

A WebSocket service on bare Node: `ws` is the only dependency, the HTTP side is
node's own `http` module, and the whole test suite is `node --test`.

## What is here

| Path | What lives there |
| --- | --- |
| `src/counts.js` | byte-exact line/word/byte counting over UTF-8 |
| `src/protocol.js` | frame parsing and the stats/ping/error handlers — pure, no sockets |
| `src/room.js` | presence: who is connected, and the frames a join or leave broadcasts |
| `src/server.js` | `http` server for `/health`, the `upgrade` handler that only accepts `/ws`, and the `ws` wiring |
| `src/main.js` | PORT/HOST, the listen call and the SIGTERM drain |
| `tools/contract.mjs` | the live contract checker: two real clients, presence, stats, errors |
| `tests/*.test.js` | `node --test` suite, including a live server on port 0 |

## Run it

```bash
npm install
node src/main.js            # ws://127.0.0.1:8080/ws
npm test
PORT=5453 npm run contract       # needs a server already listening
```

```bash
curl -s http://127.0.0.1:8080/health
# {"status":"ok","clients":0}
```

Frames, both directions, are text JSON:

```jsonc
{"type": "stats", "text": "a b\nc\n"}   // -> {"type":"stats","lines":2,"words":3,"bytes":6}
{"type": "ping"}                        // -> {"type":"pong"}
{"type": "nope"}                        // -> {"type":"error","code":"unknown_type","detail":"..."}
```

A join or a leave is broadcast to every open member:
`{"type":"presence","event":"join","clients":2}`.

## Traps this starter already paid for

- **`new WebSocketServer({ server })` hijacks every upgrade.** It answers any
  path that asks for `Upgrade: websocket`, so `/other` would connect happily. The
  starter uses `noServer: true` plus its own `upgrade` handler that writes a bare
  `404` response and destroys the socket for anything but `/ws`.
- **Presence has to be counted after the member is added.** `room.add()` inserts
  first and then builds the frame, otherwise the joining client is told
  `clients: 1` when it is actually the second one.
- **A close does not mean the broadcast is delivered.** `client.on("close")` fires
  after the TCP teardown, so the leave frame must be sent through `room.broadcast`
  (which checks `readyState`) and never by looping over `sockets.clients`
  yourself — the closed socket is still in that set while the handler runs.
- **`ws` is CommonJS.** `import { WebSocket } from "ws"` works through the
  package's `exports` map; importing `node_modules/ws/index.js` directly does
  not, and the error is a `SyntaxError` about named exports, not a resolution
  error.
- **`node --test` needs the files named.** `node --test tests/*.test.js` keeps the
  runner from picking up `node_modules`; `node --test` alone walks the whole tree.
- **SIGTERM has to close the clients.** `server.close()` alone waits for the open
  sockets and the process hangs until the orchestrator sends SIGKILL; close each
  client with code `1001` first, then exit.
- **Frames are counted in bytes, not characters.** `Buffer.from(text, "utf8")`
  before counting, or `héllo wörld\n` reports 12 bytes instead of 14.
