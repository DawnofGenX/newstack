"""A small MQTT client, used by the tests and by the self-checks."""

from __future__ import annotations

import socket

from .packet import (
    CONNACK,
    CONNECT,
    DISCONNECT,
    PINGREQ,
    PINGRESP,
    PUBACK,
    PUBLISH,
    SUBACK,
    UNSUBACK,
    Publish,
    encode_publish,
    packet,
    parse_publish,
    puback_of,
    utf8,
)
from .server import read_packet


class Client:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 1883,
        client_id: str = "{{ package_name }}-client",
        *,
        clean: bool = True,
        keepalive: int = 30,
        timeout: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self.clean = clean
        self.keepalive = keepalive
        self.timeout = timeout
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self._next_id = 1

    def _take_id(self) -> int:
        value = self._next_id
        self._next_id = 1 if value >= 0xFFFF else value + 1
        return value

    def send(self, data: bytes) -> None:
        self.sock.sendall(data)

    def _read(self) -> tuple[int, bytes]:
        return read_packet(self.sock)

    # -- control packets -----------------------------------------------
    def connect(self) -> int:
        flags = 0x02 if self.clean else 0x00
        body = utf8("MQTT") + bytes([4, flags]) + self.keepalive.to_bytes(2, "big")
        body += utf8(self.client_id)
        self.send(packet(CONNECT << 4, body))
        first, reply = self._read()
        if first >> 4 != CONNACK or len(reply) != 2:
            raise RuntimeError(f"expected CONNACK, got type {first >> 4}")
        return reply[1]

    def disconnect(self) -> None:
        try:
            self.send(packet(DISCONNECT << 4))
        finally:
            self.sock.close()

    def close(self) -> None:
        self.sock.close()

    def publish(
        self,
        topic: str,
        payload: bytes = b"",
        *,
        qos: int = 0,
        retain: bool = False,
        wait_for_ack: bool = True,
    ) -> int | None:
        packet_id = self._take_id() if qos else None
        message = Publish(topic=topic, payload=payload, qos=qos, retain=retain, packet_id=packet_id)
        self.send(encode_publish(message))
        if qos == 1 and wait_for_ack:
            first, body = self._read()
            if first >> 4 != PUBACK:
                raise RuntimeError(f"expected PUBACK, got type {first >> 4}")
            if puback_of(body) != packet_id:
                raise RuntimeError("PUBACK carried the wrong packet id")
        return packet_id

    def subscribe(self, *pairs: tuple[str, int]) -> list[int]:
        packet_id = self._take_id()
        body = packet_id.to_bytes(2, "big")
        for topic_filter, qos in pairs:
            body += utf8(topic_filter) + bytes([qos])
        self.send(packet(0x82, body))
        first, reply = self._read()
        if first >> 4 != SUBACK:
            raise RuntimeError(f"expected SUBACK, got type {first >> 4}")
        if int.from_bytes(reply[:2], "big") != packet_id:
            raise RuntimeError("SUBACK carried the wrong packet id")
        return list(reply[2:])

    def unsubscribe(self, *filters: str) -> None:
        packet_id = self._take_id()
        body = packet_id.to_bytes(2, "big")
        for topic_filter in filters:
            body += utf8(topic_filter)
        self.send(packet(0xA2, body))
        first, _ = self._read()
        if first >> 4 != UNSUBACK:
            raise RuntimeError(f"expected UNSUBACK, got type {first >> 4}")

    def ping(self) -> None:
        self.send(packet(PINGREQ << 4))
        first, _ = self._read()
        if first >> 4 != PINGRESP:
            raise RuntimeError(f"expected PINGRESP, got type {first >> 4}")

    # -- application messages ------------------------------------------
    def next_publish(self, timeout: float | None = None) -> Publish | None:
        """Wait for one PUBLISH; anything else is consumed and skipped."""
        self.sock.settimeout(self.timeout if timeout is None else timeout)
        try:
            while True:
                first, body = self._read()
                kind = first >> 4
                if kind == PUBLISH:
                    publish = parse_publish(first, body)
                    if publish.qos == 1 and publish.packet_id is not None:
                        self.send(packet(0x40, publish.packet_id.to_bytes(2, "big")))
                    return publish
                if kind == PUBACK:
                    puback_of(body)
        except TimeoutError:
            return None
        finally:
            self.sock.settimeout(self.timeout)

    def collect(self, expected: int, timeout: float | None = None) -> list[Publish]:
        found: list[Publish] = []
        while len(found) < expected:
            message = self.next_publish(timeout)
            if message is None:
                break
            found.append(message)
        return found

    def __enter__(self) -> Client:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.disconnect()
