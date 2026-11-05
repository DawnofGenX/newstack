"""An add-wins set: merge only ever grows the sets, never shrinks them."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Tag = tuple[str, int]


class ORSetError(ValueError):
    """An element or a state that cannot name itself."""


def _element(element: object) -> str:
    if not isinstance(element, str) or not element:
        raise ORSetError(f"an element must be a non-empty string, not {element!r}")
    return element


def _tag(payload: object) -> Tag:
    if not isinstance(payload, list) or len(payload) != 2:
        raise ORSetError(f"a tag is [node, counter], not {payload!r}")
    node, counter = payload
    if not isinstance(node, str) or not node:
        raise ORSetError("a tag needs a node name")
    if isinstance(counter, bool) or not isinstance(counter, int) or counter < 1:
        raise ORSetError(f"a tag counter must be a positive integer, not {counter!r}")
    return (node, counter)


@dataclass(frozen=True)
class ORSet:
    """Every add gets a unique tag; a remove only deletes the tags it has seen."""

    entries: dict[str, frozenset[Tag]] = field(default_factory=dict)
    tombstones: frozenset[Tag] = frozenset()
    counters: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for element, tags in self.entries.items():
            _element(element)
            for tag in tags:
                if not isinstance(tag, tuple) or len(tag) != 2:
                    raise ORSetError(f"tags of {element!r} must be (node, counter) pairs")
        for node, counter in self.counters.items():
            if not isinstance(node, str) or not node:
                raise ORSetError("a counter needs a node name")
            if isinstance(counter, bool) or not isinstance(counter, int) or counter < 0:
                raise ORSetError(f"the counter for {node!r} must be a non-negative integer")

    @classmethod
    def empty(cls) -> ORSet:
        return cls()

    def add(self, element: str, node: str) -> ORSet:
        _element(element)
        if not isinstance(node, str) or not node:
            raise ORSetError("an add needs a node: a tag with no author cannot be observed")
        counter = self.counters.get(node, 0) + 1
        tags = self.entries.get(element, frozenset()) | {(node, counter)}
        return ORSet(
            {**self.entries, element: tags},
            self.tombstones,
            {**self.counters, node: counter},
        )

    def remove(self, element: str) -> ORSet:
        _element(element)
        tags = self.entries.get(element, frozenset()) - self.tombstones
        if not tags:
            return self
        return ORSet(dict(self.entries), self.tombstones | tags, dict(self.counters))

    def contains(self, element: str) -> bool:
        return bool(self.entries.get(element, frozenset()) - self.tombstones)

    def elements(self) -> frozenset[str]:
        return frozenset(element for element in self.entries if self.contains(element))

    def tags_for(self, element: str) -> frozenset[Tag]:
        return self.entries.get(element, frozenset()) - self.tombstones

    def merge(self, other: ORSet) -> ORSet:
        names = set(self.entries) | set(other.entries)
        entries = {
            name: self.entries.get(name, frozenset()) | other.entries.get(name, frozenset())
            for name in names
        }
        nodes = set(self.counters) | set(other.counters)
        counters = {
            node: max(self.counters.get(node, 0), other.counters.get(node, 0)) for node in nodes
        }
        return ORSet(entries, self.tombstones | other.tombstones, counters)

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "or-set",
            "entries": {
                element: [list(tag) for tag in sorted(tags)]
                for element, tags in sorted(self.entries.items())
            },
            "tombstones": [list(tag) for tag in sorted(self.tombstones)],
            "counters": dict(sorted(self.counters.items())),
        }

    @classmethod
    def parse(cls, payload: object) -> ORSet:
        if not isinstance(payload, dict) or payload.get("type") != "or-set":
            raise ORSetError(f"not an or-set state: {payload!r}")
        raw_entries = payload.get("entries")
        raw_tombstones = payload.get("tombstones")
        raw_counters = payload.get("counters")
        if not isinstance(raw_entries, dict):
            raise ORSetError("or-set entries must be an object of element -> tags")
        if not isinstance(raw_tombstones, list):
            raise ORSetError("or-set tombstones must be a list of tags")
        entries = {
            element: frozenset(_tag(tag) for tag in tags)
            for element, tags in raw_entries.items()
            if isinstance(tags, list)
        }
        if len(entries) != len(raw_entries):
            raise ORSetError("or-set entries must map every element to a list of tags")
        return cls(
            entries, frozenset(_tag(tag) for tag in raw_tombstones), dict(raw_counters or {})
        )


@dataclass(frozen=True)
class PlainSet:
    """The wrong way: a set merged by union, where a remove is only a local opinion."""

    elements: frozenset[str] = frozenset()

    @classmethod
    def empty(cls) -> PlainSet:
        return cls()

    def add(self, element: str) -> PlainSet:
        return PlainSet(self.elements | {_element(element)})

    def remove(self, element: str) -> PlainSet:
        _element(element)
        return PlainSet(self.elements - {element})

    def merge(self, other: PlainSet) -> PlainSet:
        return PlainSet(self.elements | other.elements)

    def contains(self, element: str) -> bool:
        return element in self.elements

    def as_dict(self) -> dict[str, Any]:
        return {"type": "plain-set", "elements": sorted(self.elements)}
