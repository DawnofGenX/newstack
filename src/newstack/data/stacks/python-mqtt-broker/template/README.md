# {{ title }}

An MQTT 3.1.1 broker in one process, with no dependencies beyond the standard
library: sessions, wildcard subscriptions, retained messages and QoS 0/1
delivery, plus a small client used by the tests.

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m {{ package_name }} --selftest     # 72 checks over real sockets
.venv/bin/python -m {{ package_name }} --port 5488
bash smoke.sh                                         # driven by mosquitto_pub/sub
```

| Packet | Direction | Notes |
| --- | --- | --- |
| CONNECT / CONNACK | client → broker | protocol level 4 only |
| PUBLISH | both | QoS 0 and 1, `retain`, `dup` bit preserved |
| PUBACK | both | QoS 1 acknowledgement |
| SUBSCRIBE / SUBACK | client → broker | `0x80` refuses one filter, the session lives |
| UNSUBSCRIBE / UNSUBACK | client → broker | |
| PINGREQ / PINGRESP | client → broker | keeps a keepalive of `1.5 ×` seconds honest |
| DISCONNECT | client → broker | a clean goodbye; anything else is a protocol error |

Not implemented: QoS 2, wills, usernames and passwords, TLS, shared
subscriptions, `$SYS` topics, persistence across restarts.

## Traps this starter already paid for

1. **SUBACK goes out before the retained replay.** The broker used to deliver
   retained messages inside `subscribe()`, so a client that reads exactly one
   reply per call got a `PUBLISH` where it expected its `SUBACK`. The session is
   now granted first, the `SUBACK` is written, and only then are the parked
   messages replayed (`grant()` then `replay_retained()`).
2. **`a/#` also matches `a`.** The `#` wildcard covers the parent level, which
   is easy to miss when the matcher is written as a prefix test.
3. **A retained publish needs QoS 1 in a test.** QoS 0 is not acknowledged, so
   asserting the retained store straight after the send races the server thread;
   the check passes locally and flakes under load.
4. **A close with unread bytes arrives as a reset.** When the broker drops a
   connection that still has bytes in its receive buffer, the peer sees
   `ConnectionResetError`, not a clean end of stream. Assert "closed" for both.
5. **`mosquitto_sub` terminates what it prints with a newline.** A binary
   payload comparison must trim that byte, or every payload looks one byte too
   long.
6. **Only `-F '%t|%p|%r'` shows the retain flag.** Without it a retained
   delivery is indistinguishable from a live one.
7. **An empty retained publish is still delivered.** `-r -n` deletes the stored
   record *and* sends an empty message to the current subscribers.
8. **Packet ids belong to the connection that writes them.** A QoS 1 delivery
   to a subscriber uses that subscriber's id space, never the publisher's.
9. **An empty client id requires a clean session.** Otherwise the handshake is
   refused with CONNACK `0x02`, and a second connection that reuses a live id
   gets the same code.
10. **The remaining-length field is seven bits per byte with a continuation
    bit.** A 20 KB payload needs three length bytes; `len(body)` in one byte
    works for every small test and fails on the first real message.
