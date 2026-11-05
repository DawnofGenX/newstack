# {{ package_name }}

Zero-dependency RFC 6455 WebSocket service. Python stdlib only (`socket`,
`socketserver`, `hashlib`, `base64`, `json`, `signal`, `argparse`). No runtime
dependencies; `pytest`/`ruff` live in the `dev` extra.

## Layout

```
pyproject.toml            hatchling build, script {{ npm_name }} = {{ package_name }}.cli:main
src/{{ package_name }}/
  __init__.py             re-exports
  handshake.py            HTTP upgrade -> 101, rejections 404/400/426/405
  frames.py               RFC 6455 frame codec (7/16/64-bit lengths, masking)
  connection.py           connection loop: fragmentation, control frames, limits
  protocol.py             JSON app protocol (stats/echo/ping + error replies)
  server.py               threaded TCP server on :5489 (default)
  client.py               masking WSClient for tests/smoke (send_text/send_binary/
                          send_ping/receive/close)
  selftest.py             35+ real-socket checks -> `selftest: N checks, 0 failed`
  cli.py                  --host/--port/--selftest, PORT env, signal drain
  __main__.py             python -m {{ package_name }}
tests/test_protocol.py    pytest suite over a live server on port 0
smoke.sh                  end-to-end: rejection, round trips, fragmentation,
                          unmasked->1002, clean close, port hygiene
```

## Run

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m {{ package_name }} --selftest          # 35+ checks, exit!=0 on failure
.venv/bin/{{ npm_name }} --port 5489 &              # serve (PORT env also honored)
bash smoke.sh                                  # needs 5489 free
.venv/bin/pytest -q                            # 18+ cases, port 0
.venv/bin/ruff check .
```

## Wire contract summary

- `GET /ws` + `Upgrade: websocket` + `Connection: Upgrade` + key +
  `Sec-WebSocket-Version: 13` -> `101` with
  `Sec-WebSocket-Accept: base64(sha1(key + GUID))`.
- Plain HTTP rejections: path != `/ws` -> 404; missing/incorrect upgrade headers
  -> 400; version != 13 -> 426 (+ `Sec-WebSocket-Version: 13`); non-GET on `/ws`
  -> 405.
- Client frames MUST be masked; RSV bits, unknown opcodes, control frames with
  FIN=0 or payload >125 -> close 1002. Text must be valid UTF-8 (else 1007).
  Messages >64 KiB -> 1009. Binary application frames -> 1003.
- Close echoes the received code (default 1000); 1-byte payload or invalid code
  -> 1002. Ping answers Pong with identical payload.
- App protocol (JSON text): `stats` counts bytes over raw UTF-8 and splits words
  on `` \t\n\r\v\f `` exactly; `héllo wörld\n` = 1 line / 2 words / 14 bytes.

## Traps this starter already paid for

- **README before install**: hatchling refuses `pip install -e .` without
  `README.md` on disk (pyproject points at it via `readme =`), so the README is
  part of the committed tree, not an afterthought.
- **`| head` under `pipefail`**: closing `head` early SIGPIPE-kills the producer
  and `set -o pipefail` turns it into a failed step. `smoke.sh` writes long
  output to files or appends `|| true` instead.
- **`curl` on a 101 never returns**: a plain-HTTP probe that accidentally upgrades keeps
  reading the socket forever, so every `curl` here carries `--max-time 5`. The one
  assertion that must observe a rejection is exactly the one a broken handshake can
  turn into a hang.
- **Stale port guard**: a leftover server on 5489 makes every downstream check
  lie. `smoke.sh` probes 5489 first and bails with a named message before
  touching it, and the EXIT trap kills only the PID it started (TERM, 20x0.1s
  poll, then KILL, `wait ... || true`).
- **Server->client frames must NOT be masked**, client->server MUST be: RFC 6455
  asymmetry is the top source of "works in tests, dies in smoke" bugs, so the
  codec takes an explicit `mask=` flag per direction and the server rejects
  unmasked input with 1002.
- **Close frame code is 2 big-endian bytes**, not ASCII digits, and a bare
  1-byte payload is a protocol error (1002), not "missing code". The 1000
  default applies only to a 0-byte payload.
- **Word separators are exactly** ``space \t \n \r \v \f``: Python's
  `str.split()` also splits on \x1c-\x1f and \x85, which silently changes counts.
  `protocol.py` splits via an explicit character set instead.
- **64 KiB limit is per message**, counted across fragments (64 KiB passes,
  64 KiB+1 closes 1009) - checking per-frame instead of per-message breaks
  fragmented uploads.
- **The 64 KiB boundary is measured on the JSON message, not the padding**:
  `json.dumps({"type": "echo", "text": ""})` is 27 bytes (`, ` and `: `
  separators), so a test built with a hand-typed 25-byte literal sent
  65538-byte messages and failed its own "exactly 64 KiB" case. Compute the
  wrap length with `len(_wrap(""))`, never by hand.
- **`python -m {{ package_name }} --selftest` must exit non-zero on failure** - the checks
  print `selftest: N checks, 0 failed` and the process exit code is the contract
  for CI, not stdout parsing.
