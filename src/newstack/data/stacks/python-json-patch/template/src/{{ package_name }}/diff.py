"""Turning two documents into a patch that provably reproduces the second.

The patch is not minimal — a smaller one may exist — but it is correct by
construction, and the demo checks that applying it to the first document gives
back the second, byte for byte.
"""

from __future__ import annotations

import json
from typing import Any

from .patch import apply, equal
from .pointer import render


def _walk(before: Any, after: Any, parts: tuple[str, ...], operations: list[dict]) -> None:
    if equal(before, after):
        return
    if isinstance(before, dict) and isinstance(after, dict):
        for key in before:
            if key not in after:
                operations.append({"op": "remove", "path": render((*parts, key))})
        for key in after:
            if key not in before:
                operations.append({"op": "add", "path": render((*parts, key)), "value": after[key]})
            else:
                _walk(before[key], after[key], (*parts, key), operations)
        return
    if isinstance(before, list) and isinstance(after, list):
        common = min(len(before), len(after))
        for position in range(common):
            _walk(before[position], after[position], (*parts, str(position)), operations)
        for position in range(len(before) - 1, common - 1, -1):
            operations.append({"op": "remove", "path": render((*parts, str(position)))})
        for position in range(common, len(after)):
            operations.append(
                {"op": "add", "path": render((*parts, "-")), "value": after[position]}
            )
        return
    operations.append({"op": "replace", "path": render(parts), "value": after})


def diff(before: Any, after: Any) -> list[dict]:
    """Operations that turn `before` into `after`."""
    operations: list[dict] = []
    _walk(before, after, (), operations)
    return operations


def round_trips(before: Any, after: Any) -> bool:
    """The check that matters: apply the diff and compare."""
    return equal(apply(before, diff(before, after)), after)


def summary(operations: list[dict]) -> list[str]:
    """One line per operation, for a human reading a diff."""
    lines: list[str] = []
    for index, operation in enumerate(operations, start=1):
        path = operation.get("path", "")
        where = path or "(root)"
        name = operation.get("op")
        line = f"{index:>3}. {name:<8} {where}"
        if name in ("add", "replace", "test"):
            line += f"  {json.dumps(operation.get('value'))}"
        elif name in ("move", "copy"):
            line += f"  from {operation.get('from') or '(root)'}"
        lines.append(line)
    return lines
