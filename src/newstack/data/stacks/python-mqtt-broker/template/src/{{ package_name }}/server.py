"""A threaded TCP listener that speaks MQTT 3.1.1 to each connection."""

from __future__ import annotations

import contextlib
import logging
import socket
import threading

from .broker import Broker, DuplicateClientId, Session
from .packet import (
    BAD_CLIENT_ID,
    BAD_PROTOCOL,
    CONNECT,
    DISCONNECT,
    PINGREQ,
    PUBACK,
    PUBLISH,
    SUB_FAILURE,
    SUBSCRIBE,
    UNSUBSCRIBE,
    Connect,
    ProtocolError,
    connack,
    parse_connect,
    parse_publish,
    parse_subscribe,
    parse_unsubscribe,
    pingresp,
    puback_of,
    publish_ack,
    suback,
    unsuback,
)
from .topics import check_publish_topic

LOG = logging.getLogger("{{ package_name }}")

MAX_PACKET = 256 * 1024
CONNECT_TIMEOUT = 10.0


def read_exactly(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("the peer closed the connection")
        chunks += chunk
    return bytes(chunks)


def read_packet(sock: socket.socket) -> tuple[int, bytes]:
    """One whole control packet: first byte, then a varint, then the body."""
    first = read_exactly(sock, 1)[0]
    length = 0
    multiplier = 1
    for _ in range(4):
        digit = read_exactly(sock, 1)[0]
        length += (digit & 0x7F) * multiplier
        if not digit & 0x80:
            break
        multiplier *= 128
    else:
        raise ProtocolError("remaining length is longer than four bytes")
    if length > MAX_PACKET:
        raise ProtocolError(f"a packet of {length} bytes is larger than {MAX_PACKET}")
    return first, read_exactly(sock, length) if length else b""


class Connection:
    """One client socket, one reader thread, one lock around the writer."""

    def __init__(self, sock: socket.socket, broker: Broker, address: tuple[str, int]) -> None:
        self.sock = sock
        self.broker = broker
        self.address = address
        self.session: Session | None = None
        self._write_lock = threading.Lock()

    def send(self, data: bytes) -> None:
        with self._write_lock:
            self.sock.sendall(data)

    def _handshake(self) -> Connect | None:
        self.sock.settimeout(CONNECT_TIMEOUT)
        first, body = read_packet(self.sock)
        if first >> 4 != CONNECT:
            raise ProtocolError("the first packet must be CONNECT")
        connect = parse_connect(body)
        if connect.protocol_level != 4:
            self.send(connack(False, BAD_PROTOCOL))
            return None
        if not connect.client_id:
            if not connect.clean_session:
                self.send(connack(False, BAD_CLIENT_ID))
                return None
            connect = Connect(
                client_id=f"auto-{address_id(self.address)}",
                clean_session=True,
                keepalive=connect.keepalive,
            )
        return connect

    def serve(self) -> None:
        try:
            connect = self._handshake()
            if connect is None:
                return
            try:
                session = self.broker.attach(connect.client_id, connect.clean_session, self.send)
            except DuplicateClientId:
                self.send(connack(False, BAD_CLIENT_ID))
                return
            self.session = session
            self.send(connack(False))
            self.sock.settimeout(connect.keepalive * 1.5 if connect.keepalive else None)
            self._loop()
        except (TimeoutError, ProtocolError, ConnectionError, OSError) as error:
            LOG.debug("%s: %s", self.address, error)
        finally:
            if self.session is not None:
                self.broker.detach(self.session)
            with contextlib.suppress(OSError):
                self.sock.close()

    def _loop(self) -> None:
        assert self.session is not None
        while True:
            first, body = read_packet(self.sock)
            kind = first >> 4
            if kind == PUBLISH:
                self._publish(first, body)
            elif kind == PUBACK:
                puback_of(body)  # a broker that never retries has nothing to do here
            elif kind == SUBSCRIBE:
                packet_id, wanted = parse_subscribe(body)
                codes = [self.broker.grant(self.session, sub.filter, sub.qos) for sub in wanted]
                # SUBACK first: a client that reads one reply at a time must
                # see the grant before the retained messages it asks for.
                self.send(suback(packet_id, codes))
                for sub, granted in zip(wanted, codes, strict=True):
                    if granted != SUB_FAILURE:
                        self.broker.replay_retained(self.session, sub.filter, granted)
            elif kind == UNSUBSCRIBE:
                packet_id, filters = parse_unsubscribe(body)
                for topic_filter in filters:
                    self.broker.unsubscribe(self.session, topic_filter)
                self.send(unsuback(packet_id))
            elif kind == PINGREQ:
                self.send(pingresp())
            elif kind == DISCONNECT:
                return
            else:
                raise ProtocolError(f"packet type {kind} is not allowed from a client")

    def _publish(self, first: int, body: bytes) -> None:
        assert self.session is not None
        publish = parse_publish(first, body)
        check_publish_topic(publish.topic)
        self.broker.publish(publish.topic, publish.payload, publish.qos, publish.retain)
        if publish.qos == 1 and publish.packet_id is not None:
            self.send(publish_ack(publish.packet_id))


def address_id(address: tuple[str, int]) -> str:
    return f"{address[0].replace('.', '-')}-{address[1]}"


class Server:
    """Bind, accept, and hand each socket a thread."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 0, *, broker: Broker | None = None
    ) -> None:
        self.host = host
        self._port = port
        self.broker = broker or Broker()
        self._listener: socket.socket | None = None
        self._connections: list[Connection] = []
        self._threads: list[threading.Thread] = []
        self._stopping = threading.Event()

    @property
    def port(self) -> int:
        return self._port

    def start(self) -> Server:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self._port))
        listener.listen(64)
        listener.settimeout(0.2)
        self._listener = listener
        self._port = listener.getsockname()[1]
        thread = threading.Thread(target=self._accept_loop, name="accept", daemon=True)
        thread.start()
        self._threads.append(thread)
        return self

    def _accept_loop(self) -> None:
        assert self._listener is not None
        while not self._stopping.is_set():
            try:
                sock, address = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            connection = Connection(sock, self.broker, address)
            self._connections.append(connection)
            thread = threading.Thread(target=connection.serve, daemon=True)
            thread.start()
            self._threads.append(thread)

    def shutdown(self) -> None:
        self._stopping.set()
        if self._listener is not None:
            self._listener.close()
            self._listener = None
        for connection in self._connections:
            with contextlib.suppress(OSError):
                connection.sock.shutdown(socket.SHUT_RDWR)
            with contextlib.suppress(OSError):
                connection.sock.close()
        for thread in self._threads:
            thread.join(timeout=5)

    def __enter__(self) -> Server:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.shutdown()


def parse_port(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"PORT must be a number, got {raw!r}") from None
    if not 0 < value < 65_536:
        raise ValueError(f"PORT must be between 1 and 65535, got {value}")
    return value
