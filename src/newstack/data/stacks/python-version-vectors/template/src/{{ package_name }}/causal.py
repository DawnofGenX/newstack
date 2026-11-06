"""Causal delivery: a message waits until everything it depends on has arrived.

The vector does the work here. A message carries the sender's state at send time, so a
receiver can ask one question - "do I already hold everything this message depends on?"
- and the answer is a comparison of vectors, not a guess about clocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .vector import VersionVector


class CausalError(ValueError):
    """A message or replica that cannot be built."""


@dataclass(frozen=True)
class Message:
    """One message: who sent it, to whom, what it carries, and what it depended on."""

    id: int
    sender: str
    target: str
    deps: VersionVector
    body: str

    def __post_init__(self) -> None:
        if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id < 1:
            raise CausalError(f"a message id is a whole number of at least 1, not {self.id!r}")
        for name, value in (("sender", self.sender), ("target", self.target)):
            if not isinstance(value, str) or not value:
                raise CausalError(f"a message needs a {name}")
        if self.sender == self.target:
            raise CausalError(
                f"a message from {self.sender} to itself is a local event, not a message"
            )

    def text(self) -> str:
        deps = self.deps.text() or "none"
        return f"m{self.id} {self.sender}->{self.target} deps[{deps}] {self.body}"


@dataclass(frozen=True)
class Local:
    """A local event: no target, because nothing leaves this replica."""

    id: int
    node: str
    state: VersionVector
    body: str

    def __post_init__(self) -> None:
        if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id < 1:
            raise CausalError(f"a local event id is a whole number of at least 1, not {self.id!r}")
        if not isinstance(self.node, str) or not self.node:
            raise CausalError("a local event needs a node name")

    def text(self) -> str:
        return f"L{self.id} {self.node} state[{self.state.text() or 'none'}] {self.body}"


@dataclass
class Ids:
    """A shared counter, so two replicas never mint the same message id."""

    next_id: int = 1

    def take(self) -> int:
        number = self.next_id
        self.next_id += 1
        return number


@dataclass
class Replica:
    """A replica whose delivery either waits for dependencies (`gated`) or does not."""

    node: str
    gated: bool = True
    state: VersionVector = field(default_factory=VersionVector.empty)
    delivered: list[Message] = field(default_factory=list)
    held: list[Message] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)
    ids: Ids = field(default_factory=Ids)

    def __post_init__(self) -> None:
        if not isinstance(self.node, str) or not self.node:
            raise CausalError("a replica needs a node name")

    def local(self, body: str) -> Local:
        """A local event: it advances this replica's own counter, nothing else."""
        self.state = self.state.increment(self.node)
        return Local(self._take(), self.node, self.state, body)

    def send(self, target: str, body: str) -> Message:
        """A send carries the state *after* being recorded, which is what makes it causal."""
        self.state = self.state.increment(self.node)
        return Message(self._take(), self.node, target, self.state, body)

    def _take(self) -> int:
        return self.ids.take()

    def ready(self, message: Message) -> bool:
        """Everything the message depends on, except its own send, must already be here."""
        needed = message.deps
        own = needed.get(message.sender) - 1
        rest = VersionVector(
            {node: count for node, count in needed.counts().items() if node != message.sender}
        )
        return self.state.dominates(rest) and self.state.get(message.sender) >= own

    def receive(self, message: Message) -> str:
        """Deliver, hold, or - if it is not gated - deliver something it should hold."""
        if self.gated and not self.ready(message):
            self.held.append(message)
            return "held"
        self._deliver(message)
        return "delivered"

    def _deliver(self, message: Message) -> None:
        self.delivered.append(message)
        merged = self.state.merge(message.deps)
        self.state = VersionVector(
            {**merged.counts(), message.sender: message.deps.get(message.sender)}
        )
        self.counters = {node: self.state.get(node) for node in self.state.nodes()}

    def drain(self) -> list[Message]:
        """Deliver whatever the arrival of one message made ready, until nothing is left."""
        released: list[Message] = []
        progress = True
        while progress:
            progress = False
            for message in list(self.held):
                if self.ready(message):
                    self.held.remove(message)
                    self._deliver(message)
                    released.append(message)
                    progress = True
        return released


def causality_violations(delivered: list[Message]) -> list[tuple[Message, str, int, int]]:
    """Deliveries that arrived before something they depended on.

    A message that depends on `n` events from a sender must be delivered after that
    sender's nth event. This walks a delivery order and reports every entry that
    outran its dependencies, with the counter it needed and the counter it had.
    """
    seen: dict[str, int] = {}
    broken: list[tuple[Message, str, int, int]] = []
    for message in delivered:
        for node, count in message.deps.counts().items():
            needed = count - 1 if node == message.sender else count
            had = seen.get(node, 0)
            if had < needed:
                broken.append((message, node, needed, had))
        seen[message.sender] = max(seen.get(message.sender, 0), message.deps.get(message.sender))
    return broken


def describe_violations(broken: list[tuple[Message, str, int, int]]) -> list[str]:
    """One line per break, in the form a reader can check against the transcript."""
    return [
        f"m{message.id} {message.sender}->{message.target} needed {node} at {needed}, had {had}"
        for message, node, needed, had in broken
    ]
