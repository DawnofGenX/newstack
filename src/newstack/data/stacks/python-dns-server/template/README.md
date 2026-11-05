# {{ npm_name }}

An authoritative DNS server for one small zone, over UDP and TCP, with no
runtime dependencies: the wire format, the zone lookup and both transports are
written against the standard library.

```
make-like flow                 what it shows
uv venv --allow-existing       an isolated interpreter
uv pip install -e ".[dev]"     the package plus pytest and ruff
.venv/bin/python -m pytest -q  28 tests over real sockets
.venv/bin/python -m {{ package_name }} --selftest   44 checks, no pytest needed
PY=.venv/bin/python bash smoke.sh                  20 checks, judged by dig
```

## Contract

`{{ npm_name }} --port 5487` answers on UDP and TCP on the same port.

| query | answer |
| --- | --- |
| `www.<apex> A` | every A record at the name, in zone order |
| `alias.<apex> A` | the CNAME, then the records it points at |
| `<apex> AAAA/TXT/MX/NS/SOA` | the record text dig normally shows |
| `ANY` | every record at the name |
| unknown name under the apex | `NXDOMAIN`, authoritative, SOA in authority |
| known name, missing type | `NOERROR`, no answer, SOA in authority |
| name outside the apex | `REFUSED`, not authoritative |
| class other than IN, opcode other than QUERY | `NOTIMP` |
| packet too short to parse | dropped, or a bare `FORMERR` header |
| answer larger than the datagram allows | `TC` set, question only, no records |

`--selftest` runs the same checks on an ephemeral port and exits non-zero on the
first failure; `--apex` changes the zone name.

## Traps this starter already paid for

1. **Port 0 picks two ports.** Binding UDP and TCP separately with port 0 gives
   two different ephemeral ports, so the reported port only answers UDP and
   every TCP client gets `ECONNREFUSED`. Bind UDP first, read the port back,
   then bind TCP to that number.
2. **EDNS0 raises the ceiling, it does not lower it.** The sender's advertised
   payload size arrives in the OPT record's CLASS field; taking `min(server,
   client)` unconditionally keeps every datagram at 512 bytes and truncates
   answers the client was ready to receive.
3. **A truncated datagram is not the end of the story for dig.** `dig` retries
   over TCP automatically and prints the TCP answer, so a truncation check
   without `+ignore` silently asserts the full answer.
4. **A CNAME belongs in the answer.** Following the chain without emitting the
   CNAME record gives a client an answer it cannot cache correctly and hides
   the indirection the query asked about.
5. **Compression pointers must not be trusted.** A pointer that does not point
   backwards, or a chain of them, is a format error: follow at most a handful
   of hops and cap the assembled name at 255 bytes.
6. **TXT rdata is chunked, not a string.** Each chunk carries its own length
   byte and chunks are capped at 255 bytes, so anything longer than that has to
   be split on the way out and joined on the way in.
7. **`socket.SOCK_UDP` does not exist.** The constant is `SOCK_DGRAM`; using the
   wrong name raises `AttributeError` inside a readiness probe, which reads
   exactly like "the server is not listening" when stderr is discarded.
8. **A name in a log line can outgrow the line limit.** Keep the program name in
   one constant (`PROG`) so render-time renaming cannot push a message past the
   project's line-length gate.
