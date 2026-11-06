"""The page file: one tree frozen into fixed-size records, read back identical.

`write_page` walks the tree once and writes a header plus one record per node:
depth, key count, child count, then keys and child slots padded to the width
the order demands. `read_page` rebuilds the nodes and re-links the slots, so
the clone walks to the same sorted corpus — after any insert AND delete
history, not only after a clean build.

A node is written once and named by its slot, so the file reads in one pass
whatever order the walk produced. The header names the order; a reader never
has to guess how wide a record is.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .btree import BTree

__all__ = ["PageError", "PageReport", "read_page", "write_page"]

MAGIC = b"BTREE1"
HEADER = 18  # magic, order, node count, pad
MAX_NODES = 4096


class PageError(ValueError):
    """A page file could not be written or read."""


@dataclass(frozen=True)
class PageReport:
    """What one write/read pair cost and proved."""

    nodes: int
    record: int
    width: int
    identical: bool

    def lines(self) -> list[str]:
        return [
            f"nodes      {self.nodes}",
            f"record     {self.record} byte(s), file {self.width} byte(s)",
            f"identical  {self.identical}",
        ]


def record_width(order: int) -> int:
    """Bytes per node: shape header, padded keys, padded child slots."""
    return 6 + 4 * (2 * order - 1) + 8 * order


def _listing(tree: BTree) -> list[tuple[int, list[int], list[int]]]:
    """Flatten the tree in-order: each node as (depth, keys, child slots)."""
    found: list[tuple[int, list[int], list[int]]] = []
    handles: dict[int, int] = {}

    def walk(node: object, depth: int) -> None:
        slot = len(found)
        handles[id(node)] = slot
        found.append((depth, list(node.keys), []))  # type: ignore[attr-defined]
        for child in node.children:  # type: ignore[attr-defined]
            walk(child, depth + 1)
        found[slot] = (
            depth,
            found[slot][1],
            [handles[id(child)] for child in node.children],  # type: ignore[attr-defined]
        )

    walk(tree._root, 0)
    return found


def write_page(tree: BTree, path: str | Path) -> int:
    """Freeze `tree` into a page file. Returns the node count written."""
    nodes = _listing(tree)
    if len(nodes) > MAX_NODES:
        raise PageError(f"{len(nodes)} nodes will not fit in {MAX_NODES} slots")
    keys = 4 * (2 * tree.order - 1)
    children = 8 * tree.order
    location = Path(path)
    try:
        with open(location, "wb") as handle:
            handle.write(MAGIC + struct.pack(">ii", tree.order, len(nodes)) + b"\0\0\0\0")
            for depth, held, slots in nodes:
                body = struct.pack(">hhh", depth, len(held), len(slots))
                body += b"".join(struct.pack(">i", key) for key in held)
                body += b"\0" * (keys - 4 * len(held))
                body += b"".join(struct.pack(">i", slot) for slot in slots)
                body += b"\0" * (children - 4 * len(slots))
                handle.write(body)
    except OSError as error:
        raise PageError(str(error)) from error
    return len(nodes)


def read_page(path: str | Path) -> BTree:
    """Rebuild the tree a page file holds, shape included."""
    from . import btree as module

    location = Path(path)
    if not location.exists():
        raise PageError(f"no such page file: {location}")
    data = location.read_bytes()
    if len(data) < HEADER or not data.startswith(MAGIC):
        raise PageError(f"{location} is not a page file")
    order, count = struct.unpack(">ii", data[6:14])
    width = record_width(order)
    if len(data) != HEADER + width * count:
        raise PageError(f"{len(data)} bytes is not {count} records of {width}")
    keys = 4 * (2 * order - 1)
    bodies: list[tuple[list[int], list[int]]] = []
    for slot in range(count):
        start = HEADER + width * slot
        _, key_count, child_count = struct.unpack(">hhh", data[start : start + 6])
        held = [
            struct.unpack(">i", data[start + 6 + 4 * i : start + 10 + 4 * i])[0]
            for i in range(key_count)
        ]
        slots = [
            struct.unpack(
                ">i", data[start + 6 + keys + 4 * i : start + 10 + keys + 4 * i]
            )[0]
            for i in range(child_count)
        ]
        bodies.append((held, slots))
    tree = BTree(order)
    rebuilt = [module._Node(keys=list(held)) for held, _ in bodies]
    for (_, slots), node in zip(bodies, rebuilt, strict=True):
        node.children = [rebuilt[slot] for slot in slots]
    tree._root = rebuilt[0] if rebuilt else module._Node()
    return tree


def page_pair(tree: BTree, path: str | Path) -> PageReport:
    """Write, read back, and compare the walk: the falsifiable claim."""
    nodes = write_page(tree, path)
    clone = read_page(path)
    identical = clone.keys == tree.keys and [
        shape.keys for shape in clone.shape()
    ] == [shape.keys for shape in tree.shape()]
    width = Path(path).stat().st_size
    return PageReport(nodes, record_width(tree.order), width, identical)
