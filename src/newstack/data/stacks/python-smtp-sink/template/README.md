# a capturing SMTP sink

Point a development app at `127.0.0.1:5482` and every message it sends becomes a
readable `.eml` file plus one line in `index.ndjson`.

```
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m {{ package_name }}.cli serve --port 5482 --mailbox mailbox
.venv/bin/python -m {{ package_name }}.cli list --mailbox mailbox --json
.venv/bin/python -m {{ package_name }}.cli rebuild --mailbox mailbox
```

## Contract

| situation | answer |
| --- | --- |
| any message under the size limit | `250 Message accepted for delivery`, stored as `.eml` |
| message larger than `--size-limit` | `552` at `MAIL FROM` (with EHLO SIZE) or at `DATA`, never stored |
| recipient named by `--reject` | `550 mailbox unavailable`, nothing stored |
| 8-bit headers or body | accepted: the controller runs with `enable_SMTPUTF8=True` |

`list --json` prints the index; `rebuild` recreates the index from the `.eml`
files, because the files are the truth.

## Traps this starter already paid for

1. **`Controller(port=0)` does not work.** aiosmtpd probes "is the server up"
   by connecting to `self.port`, which is `0`, and `start()` raises
   `ConnectionRefusedError` before the server is reachable. The sink binds a
   probe socket, reads the free port and releases it (`free_port()`).
2. **The size limit can be enforced at `MAIL FROM`.** With EHLO `SIZE`
   advertised, an oversized message is refused with `SMTPSenderRefused`, not
   `SMTPDataError`; tests must accept either shape of the same `552`.
3. **Dot-stuffing is a wire encoding, not content.** A line `.hidden` arrives
   with an extra dot and must be unstuffed back; scanning the stored bytes for
   `..` proves nothing. Parse the stored message and compare the payload.
4. **Store, then index.** The `.eml` is written to a `.part` file and renamed
   before the index line is appended and `fsync`ed, so a crash leaves a message
   without an index entry (recoverable with `rebuild`), never a half-written
   message.
5. **A torn index line is data, not a bug.** The last line can be truncated by
   a crash; `messages()` skips anything that is not JSON instead of raising.
6. **Header decoding needs the MIME decoder.** A UTF-8 subject arrives
   RFC 2047-encoded (`=?utf-8?b?…?=`); `Subject` must go through
   `decode_header`/`make_header` or the index shows base64.
7. **`stop()` must be called from the same thread that started it**, and the
   smoke script waits for the process to exit before checking the port, or the
   next run finds `EADDRINUSE`.
