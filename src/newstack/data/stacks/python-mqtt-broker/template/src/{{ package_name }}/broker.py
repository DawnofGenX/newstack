"""The topic tree: sessions, subscriptions, retained messages, delivery."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from .packet import SUB_FAILURE, Publish, encode_publish
from .topics import matches, valid_filter

Sender = Callable[[bytes], None]


@dataclass
class Session:
    client_id: str
    clean: bool
    subscriptions: dict[str, int] = field(default_factory=dict)
    sender: Sender | None = None
    closer: Callable[[], None] | None = None
    next_packet_id: int = 1
    closed: bool = False

    def shutdown(self) -> None:
        """Close the socket behind this session; used when an id is taken over."""
        self.closed = True
        self.sender = None
        if self.closer is not None:
            with contextlib.suppress(OSError):
                self.closer()

    def take_packet_id(self) -> int:
        value = self.next_packet_id
        self.next_packet_id = 1 if value >= 0xFFFF else value + 1
        return value

    def deliver(self, topic: str, payload: bytes, qos: int, retain: bool) -> bool:
        """Send one application message; False when the socket is gone."""
        if self.sender is None or self.closed:
            return False
        message = Publish(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            packet_id=self.take_packet_id() if qos else None,
        )
        try:
            self.sender(encode_publish(message))
        except OSError:
            self.closed = True
            return False
        return True


@dataclass(frozen=True)
class Delivery:
    client_id: str
    qos: int


class Broker:
    """One process, one topic tree, a lock around every mutation."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, Session] = {}
        self._retained: dict[str, tuple[bytes, int]] = {}

    # -- sessions ------------------------------------------------------
    def attach(
        self,
        client_id: str,
        clean: bool,
        sender: Sender,
        closer: Callable[[], None] | None = None,
    ) -> Session:
        """Claim a client id. A second connection takes the session over.

        MQTT 3.1.1 section 3.1.4 says the server disconnects the client that
        already holds the id, so a reconnect that arrives before the old
        socket's cleanup has run still succeeds instead of being refused.
        """
        takeover: Session | None = None
        with self._lock:
            existing = self._sessions.get(client_id)
            if existing is not None and not existing.closed:
                takeover = existing
            inherited = {} if clean or existing is None else dict(existing.subscriptions)
            session = Session(client_id, clean, inherited)
            session.sender = sender
            session.closer = closer
            self._sessions[client_id] = session
        if takeover is not None:
            takeover.shutdown()
        return session

    def detach(self, session: Session) -> None:
        with self._lock:
            session.closed = True
            session.sender = None
            if self._sessions.get(session.client_id) is not session:
                # A newer connection owns the id now; leave its session alone.
                return
            if session.clean:
                self._sessions.pop(session.client_id, None)
                # A clean session leaves nothing behind, not even subscriptions.
                session.subscriptions.clear()
            else:
                # The id keeps its subscriptions for the next connection.
                self._sessions[session.client_id] = session

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def connected(self) -> list[str]:
        with self._lock:
            return sorted(s.client_id for s in self._sessions.values() if not s.closed)

    # -- subscriptions -------------------------------------------------
    def grant(self, session: Session, topic_filter: str, qos: int) -> int:
        """Record one subscription; SUBACK has to go out before any replay."""
        if not valid_filter(topic_filter):
            return SUB_FAILURE
        granted = min(qos, 2)
        with self._lock:
            session.subscriptions[topic_filter] = granted
        return granted

    def replay_retained(self, session: Session, topic_filter: str, granted: int) -> int:
        """Send the retained messages a new filter matches; returns how many."""
        with self._lock:
            parked = [
                (topic, payload, retained_qos)
                for topic, (payload, retained_qos) in sorted(self._retained.items())
                if matches(topic_filter, topic)
            ]
        sent = 0
        for topic, payload, retained_qos in parked:
            if session.deliver(topic, payload, min(granted, retained_qos), retain=True):
                sent += 1
        return sent

    def subscribe(self, session: Session, topic_filter: str, qos: int) -> int:
        granted = self.grant(session, topic_filter, qos)
        if granted != SUB_FAILURE:
            self.replay_retained(session, topic_filter, granted)
        return granted

    def unsubscribe(self, session: Session, topic_filter: str) -> bool:
        with self._lock:
            return session.subscriptions.pop(topic_filter, None) is not None

    def subscriptions_of(self, client_id: str) -> dict[str, int]:
        with self._lock:
            session = self._sessions.get(client_id)
            return dict(session.subscriptions) if session else {}

    # -- publishing ----------------------------------------------------
    def publish(self, topic: str, payload: bytes, qos: int, retain: bool) -> list[Delivery]:
        """Route one message; returns who got it and at which QoS."""
        with self._lock:
            if retain:
                if payload:
                    self._retained[topic] = (payload, qos)
                else:
                    # An empty retained message deletes the retained record.
                    self._retained.pop(topic, None)
            targets: list[tuple[Session, int]] = []
            for session in self._sessions.values():
                if session.closed:
                    continue
                best = None
                for pattern, granted in session.subscriptions.items():
                    if matches(pattern, topic):
                        best = granted if best is None else max(best, granted)
                if best is not None:
                    targets.append((session, best))
        delivered: list[Delivery] = []
        for session, granted in targets:
            effective = min(qos, granted)
            if session.deliver(topic, payload, effective, retain=False):
                delivered.append(Delivery(session.client_id, effective))
        return delivered

    def retained(self) -> dict[str, tuple[bytes, int]]:
        with self._lock:
            return dict(self._retained)
