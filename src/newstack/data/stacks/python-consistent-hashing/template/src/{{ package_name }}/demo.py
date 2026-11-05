"""Six stories about what a ring does and a modulo does not."""

from __future__ import annotations

from collections.abc import Iterable

from .audit import histogram, mod_map, moved, only_from, percentage, summary
from .hashing import hash64
from .ring import Ring

KEYS = [f"user:{number:05d}" for number in range(5_000)]
NODES = ["alpha", "bravo", "charlie", "delta", "echo"]


def ring_with(nodes: Iterable[str], *, vnodes: int = 160) -> Ring:
    ring = Ring(vnodes=vnodes)
    for node in nodes:
        ring.add(node)
    return ring


def stories() -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []

    # 1. modulo vs ring when a node joins
    before_ring = ring_with(NODES).mapping(KEYS)
    after_ring = ring_with([*NODES, "foxtrot"]).mapping(KEYS)
    before_mod = mod_map(KEYS, NODES)
    after_mod = mod_map(KEYS, [*NODES, "foxtrot"])
    ring_moved = len(moved(before_ring, after_ring))
    mod_moved = len(moved(before_mod, after_mod))
    out.append(
        (
            "1. adding a node: modulo remaps almost everything, a ring does not",
            [
                f"  keys            {len(KEYS)}",
                f"  modulo          {mod_moved} moved ({percentage(mod_moved, len(KEYS)):.1f}%)",
                f"  ring            {ring_moved} moved ({percentage(ring_moved, len(KEYS)):.1f}%)",
                f"  the new node's fair share is one sixth, {percentage(1, 6):.1f}%",
                "  modulo has no idea what it moved: every slot changes",
            ],
        )
    )

    # 2. removing a node moves only its own keys
    full = ring_with([*NODES, "foxtrot"])
    trimmed = ring_with(NODES)
    changes = moved(full.mapping(KEYS), trimmed.mapping(KEYS))
    out.append(
        (
            "2. removing a node moves exactly the keys it owned",
            [
                f"  {summary(full.mapping(KEYS), trimmed.mapping(KEYS))}",
                f"  every one of them came from foxtrot: {only_from(changes, 'foxtrot')}",
                "  this is the property modulo cannot offer: it relocates strangers",
            ],
        )
    )

    # 3. virtual nodes decide how even the split is
    lines = [
        "  vnodes   arc imbalance   measured   min/max keys",
    ]
    for vnodes in (1, 4, 20, 160, 640):
        ring = ring_with(NODES, vnodes=vnodes)
        loads = ring.loads(KEYS)
        lines.append(
            f"  {vnodes:>6}   {ring.arc_imbalance():>13.2f}   "
            f"{ring.imbalance(KEYS):>8.2f}   {min(loads.values()):>5}/{max(loads.values()):<5}"
        )
    lines.append("  one point per node is not a ring, it is a lottery")
    lines.append("  arc imbalance is the ring's own shape; the measured column samples 5,000 keys")
    lines.append("  and stops improving once the sample, not the ring, is the limit")
    out.append(("3. virtual nodes are what make the split even", lines))

    # 4. weights follow the vnodes
    weighted = Ring(vnodes=100)
    weighted.add("small", weight=1)
    weighted.add("big", weight=3)
    shares = weighted.shares(KEYS)
    out.append(
        (
            "4. a weight is a share of the ring, and shares are measurable",
            [
                f"  small weight 1   {shares['small'] * 100:5.1f}% of keys",
                f"  big   weight 3   {shares['big'] * 100:5.1f}% of keys",
                "  weight 3 means three times the points, not three times the keys:",
                "  the share converges on 1:3 as the key count grows",
            ],
        )
    )

    # 5. insertion order does not matter
    forward = ring_with(NODES).mapping(KEYS[:500])
    backward = Ring(vnodes=160)
    for node in reversed(NODES):
        backward.add(node)
    same = forward == backward.mapping(KEYS[:500])
    out.append(
        (
            "5. the ring does not care in what order the nodes joined",
            [
                f"  forward and reversed insertion agree on all keys: {same}",
                "  the ring is sorted by where the points land, not by when they arrived",
            ],
        )
    )

    # 6. wraparound
    ring = ring_with(NODES)
    first, last = ring.points[0], ring.points[-1]
    beyond = next(
        key
        for number in range(200_000)
        for key in (f"probe:{number}",)
        if hash64(key) > last.position
    )
    out.append(
        (
            "6. the ring wraps: a key past the last point belongs to the first node",
            [
                f"  points          {len(ring.points)}",
                f"  first point     {first.text()}",
                f"  last point      {last.text()}",
                f"  {beyond} hashes past the last point",
                f"  it lands on     {ring.get(beyond)}, which is the first point again",
                "  a lookup that runs off the end and returns nothing is a dropped key",
            ],
        )
    )
    return out


def render() -> str:
    lines: list[str] = []
    for title, body in stories():
        lines.append(title)
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_table(ring: Ring, keys: Iterable[str]) -> str:
    loads = ring.loads(keys)
    total = sum(loads.values())
    return "\n".join(
        f"  {node:<10} {load:>6}  {percentage(load, total):5.1f}%" for node, load in loads.items()
    )


def histogram_line(mapping: dict[str, str]) -> str:
    return " ".join(f"{node}={count}" for node, count in histogram(mapping).items())
