"""A van Emde Boas tree over the fixed universe [0, 256).

Eight bits, four levels deep: cluster arithmetic pays the seek, and
the shipped scans still audit it. The node caches its minimum, which
may double-store the lowest cluster seat, and nothing else: a maximum
is always derived from the summary, never recounted from a cache the
clusters forgot. The structure is never trusted: `audit` recomputes
it and reports every lie it finds.
"""

from __future__ import annotations

from .keys import MAX_KEY, UNIVERSE, ensure_key

LEAF = 2                        # the bottom universe, two seats
DEFAULT_SEED = 20261107


class TreeError(ValueError):
    """An operation the tree refuses, always by naming the key."""


def _split(universe: int) -> tuple[int, int]:
    """Cluster size and cluster count for a power-of-two universe."""
    half = (universe.bit_length() - 1) // 2
    cluster = 1 << half
    return cluster, universe // cluster


class _Node:
    """One level of the tree: a min, a leaf max, clusters, a summary."""

    __slots__ = ("mini", "mn", "mx", "summary")

    def __init__(self) -> None:
        self.mn: int | None = None
        self.mx: int | None = None       # meaningful only at the leaf
        self.mini: dict[int, _Node] = {}
        self.summary: _Node | None = None


class VanEmdeTree:
    """Integers in [0, 256) with seek answers in log-log time.

    Honest about its edges: an empty tree answers min, max, succ, and
    pred with `None`, and a remove of an absent key raises `TreeError`
    with the tree untouched.
    """

    universe = UNIVERSE

    def __init__(self, keys: object = ()) -> None:
        self._root = _Node()
        self._live = 0
        for key in keys:  # type: ignore[union-attr]
            self.insert(key)

    def __len__(self) -> int:
        return self._live

    def insert(self, key: object) -> None:
        """Seat a key; seating it twice is quiet."""
        value = ensure_key(key)
        if _member(self._root, value, UNIVERSE):
            return
        _insert(self._root, value, UNIVERSE)
        self._live += 1

    def remove(self, key: object) -> None:
        """Unseat a key; an absent key raises and changes nothing."""
        value = ensure_key(key)
        if not _member(self._root, value, UNIVERSE):
            raise TreeError(f"no key {value} to remove")
        _delete(self._root, value, UNIVERSE)
        self._live -= 1

    def member(self, key: object) -> bool:
        """Whether a key sits in the tree."""
        return _member(self._root, ensure_key(key), UNIVERSE)

    def successor(self, key: object) -> int | None:
        """The smallest seat >= key, None past the last seat."""
        return _successor(self._root, ensure_key(key), UNIVERSE)

    def predecessor(self, key: object) -> int | None:
        """The largest seat <= key, None before the first seat."""
        return _predecessor(self._root, ensure_key(key), UNIVERSE)

    def minimum(self) -> int | None:
        """The smallest seat, None when the tree is empty."""
        return self._root.mn

    def maximum(self) -> int | None:
        """The largest seat, None when the tree is empty."""
        return _maximum(self._root, UNIVERSE)

    def live(self) -> list[int]:
        """Every seat in order, walked by successor from the min."""
        first = self._root.mn
        if first is None:
            return []
        keys = [first]
        probe = _successor(self._root, first + 1, UNIVERSE) if first < MAX_KEY else None
        while probe is not None:
            keys.append(probe)
            probe = (
                _successor(self._root, probe + 1, UNIVERSE) if probe < MAX_KEY else None
            )
        return keys

    def invariant(self) -> bool:
        """Whether every stored figure tells the truth."""
        return not self.audit()

    def audit(self) -> list[str]:
        """Every lie in the structure, empty when the tree is honest."""
        lies: list[str] = []
        _audit(self._root, UNIVERSE, lies)
        if self._live != len(self.live()):
            lies.append(f"size says {self._live}, the walk says {len(self.live())}")
        return lies

    def rebuild(self) -> VanEmdeTree:
        """A fresh tree from the walk, the rebuild answering alike."""
        return VanEmdeTree(self.live())


def _maximum(node: _Node, universe: int) -> int | None:
    """The highest seat, always derived, never a stale cache."""
    if node.mn is None:
        return None
    if universe == LEAF:
        return node.mx
    if not node.mini:
        return node.mn
    cluster, count = _split(universe)
    last = _maximum(node.summary, count) if node.summary else None
    if last is None:
        return node.mn
    return last * cluster + _maximum(node.mini[last], cluster)


def _insert(node: _Node, value: int, universe: int) -> None:
    """Seat a validated value the caller proved absent; leaf bottoms out."""
    if node.mn is None:
        node.mn = node.mx = value
        return
    if universe == LEAF:
        node.mn = min(node.mn, node.mx, value)
        node.mx = max(node.mn, value) if value > node.mn else node.mx
        if node.mx < node.mn:
            node.mn, node.mx = node.mx, node.mn
        return
    if value < node.mn:
        value, node.mn = node.mn, value
    cluster, count = _split(universe)
    high, low = divmod(value, cluster)
    sub = node.mini.get(high)
    if sub is None:
        sub = node.mini[high] = _Node()
        if node.summary is None:
            node.summary = _Node()
        _insert(node.summary, high, count)
    _insert(sub, low, cluster)


def _delete(node: _Node, value: int, universe: int) -> None:
    """Unseat a validated value the caller proved seated."""
    if node.mn is None:
        raise TreeError(f"no key {value} to remove")
    if universe == LEAF:
        if value == node.mn and value == node.mx:
            node.mn = node.mx = None
        elif value == node.mn:
            node.mn = node.mx
        elif value == node.mx:
            node.mx = node.mn
        else:
            raise TreeError(f"no key {value} to remove")
        return
    if not node.mini:
        if value != node.mn:
            raise TreeError(f"no key {value} to remove")
        node.mn = node.mx = None
        return
    cluster, count = _split(universe)
    target = value
    if value == node.mn:
        first = node.summary.mn if node.summary is not None else None
        if first is None:
            raise TreeError(f"clusters closed under {value} at {universe}")
        target = first * cluster + node.mini[first].mn
        node.mn = target
    high, low = divmod(target, cluster)
    sub = node.mini.get(high)
    if sub is None:
        raise TreeError(f"no key {value} to remove")
    _delete(sub, low, cluster)
    if sub.mn is None:
        del node.mini[high]
        if node.summary is None:
            raise TreeError(f"summary lost beside clusters at {universe}")
        _delete(node.summary, high, count)


def _member(node: _Node, value: int, universe: int) -> bool:
    if node.mn is None:
        return False
    if value == node.mn:
        return True
    if universe == LEAF:
        return value == node.mx
    if not node.mini:
        return False
    cluster, _count = _split(universe)
    high, low = divmod(value, cluster)
    sub = node.mini.get(high)
    return sub is not None and _member(sub, low, cluster)


def _successor(node: _Node, value: int, universe: int) -> int | None:
    if node.mn is None:
        return None
    if value <= node.mn:
        return node.mn
    top = _maximum(node, universe)
    if value > top:
        return None
    if universe == LEAF or not node.mini:
        return top
    cluster, count = _split(universe)
    high, low = divmod(value, cluster)
    sub = node.mini.get(high)
    inner = _successor(sub, low, cluster) if sub is not None else None
    if inner is not None:
        return high * cluster + inner
    if node.summary is None:
        return None
    nxt = _successor(node.summary, high + 1, count)
    if nxt is None:
        return None
    return nxt * cluster + node.mini[nxt].mn


def _predecessor(node: _Node, value: int, universe: int) -> int | None:
    if node.mn is None:
        return None
    top = _maximum(node, universe)
    if value >= top:
        return top
    if value < node.mn:
        return None
    if value == node.mn or universe == LEAF or not node.mini:
        return node.mn
    cluster, count = _split(universe)
    high, low = divmod(value, cluster)
    sub = node.mini.get(high)
    inner = _predecessor(sub, low, cluster) if sub is not None else None
    if inner is not None:
        return high * cluster + inner
    if node.summary is None:
        return node.mn
    prior = _predecessor(node.summary, high - 1, count)
    if prior is None:
        return node.mn
    return prior * cluster + _maximum(node.mini[prior], cluster)


def _audit(node: _Node, universe: int, lies: list[str]) -> None:
    """Walk the structure and collect every inconsistency."""
    if node.mn is None:
        if node.mini or (node.summary is not None and node.summary.mn is not None):
            lies.append(f"empty node {universe} carries clusters")
        if node.mx is not None:
            lies.append(f"empty node {universe} remembers a max")
        return
    if not 0 <= node.mn < universe:
        lies.append(f"node {universe} caches {node.mn} outside itself")
        return
    if universe == LEAF:
        if node.mx is None or not node.mn <= node.mx < universe:
            lies.append(f"leaf {universe} stores max {node.mx} beside min {node.mn}")
        if node.mini:
            lies.append(f"leaf {universe} clusters its seats")
        return
    if node.mx is not None and universe != LEAF and node.mini:
        pass  # a dead cache above the leaf is silence, not a lie
    cluster, count = _split(universe)
    if not node.mini:
        if node.summary is not None and node.summary.mn is not None:
            lies.append(f"node {universe} closed its clusters, kept a summary")
        return
    if node.summary is None or node.summary.mn is None:
        lies.append(f"open node {universe} seeks through a shut summary")
        return
    _audit(node.summary, count, lies)
    seated = sorted(node.mini)
    if node.summary.mn != seated[0]:
        lies.append(f"summary of {universe} opens at the wrong cluster")
    top = _maximum(node.summary, count)
    if top != seated[-1]:
        lies.append(f"summary of {universe} closes on the wrong cluster")
    if node.mn > seated[0] * cluster + node.mini[seated[0]].mn:
        lies.append(f"min of {universe} is above every clustered seat")
    for high, sub in sorted(node.mini.items()):
        if not 0 <= high < count:
            lies.append(f"cluster index {high} outside [0, {count})")
        _audit(sub, cluster, lies)
