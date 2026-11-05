# {{ project_name }}

{{ description }}

A server that never finishes its response: `GET /stream` holds the connection open
and writes one event per tick. Everything else here exists to make that safe.

## Routes

| Route | What it does |
| --- | --- |
| `GET /health` | `{"status":"ok"}` — the liveness probe, never a stream |
| `GET /stream?count=5&delay=0.05` | `count` tick events, then one `done` event |
| `GET /stats/stream?text=…&size=4` | one `chunk` event per slice, each with running totals |
| `POST /stream` | 405: a body is a request, not a subscription |

`Last-Event-ID` resumes: send the last id you saw and the stream starts after it
instead of replaying. That header is what makes a dropped connection cheap to
recover from, and it is why event ids are on the wire at all.

## Traps this starter already paid for

- **A proxy turns a stream into a slow response.** `Cache-Control: no-cache` plus
  `X-Accel-Buffering: no` is what tells nginx not to buffer the body until the
  generator finishes; without the second header the client sees nothing for the
  whole `count × delay`.
- **A test that reads the whole body proves nothing.** `TestClient` and
  `response.text` both wait for the end, so a service that builds the entire event
  list as one string passes them. `tests/test_stream.py` opens a raw socket,
  asserts the first read holds tick 1 but not tick 3, and asserts the remaining
  events took at least two delays to arrive.
- **A newline inside `data:` splits the event.** Field values are newline-free, so
  a multi-line payload repeats the field name (`data: one\ndata: two`). Joining
  the lines back with `\n` is the client's job; `wire.encode_field` exists so the
  server never forgets.
- **Comments keep the connection alive.** Buffers and load balancers time out an
  idle stream; `: stream open` at the start (and a periodic `: ping` if your ticks
  are slow) is the cheapest defence.
- **A disconnected client still costs a coroutine.** Without
  `await request.is_disconnected()` the generator keeps sleeping out the whole
  count, holding a worker slot for a socket nobody is reading.
- **Validation errors have two shapes.** FastAPI answers 422 with a list of
  pydantic errors; a stream client wants a sentence. `main.py` normalises both
  validation and HTTP errors to `{"error": …, "detail": …}` so a client can branch
  on one field.
- **Port 0 in the tests.** The socket test binds `port=0` and reads the real port
  back from `server.servers[0].sockets[0]`; a hard-coded port makes the suite fail
  whenever something else is listening.

## Run it

```bash
uv venv && uv pip install -e . pytest httpx ruff
uv run uvicorn {{ package_name }}.main:app --reload --port 5454
curl -N "http://127.0.0.1:5454/stream?count=3&delay=0.2"
```
