"""The Node major a generated project declares.

A JavaScript stack says which majors it has been proven on in ``stack.json``::

    "node": {"minimum": "22", "versions": ["22", "24"]}

``--node`` moves the floor up — never below the stack's own minimum — and every
place the version is written (the ``engines`` field, the CI matrix, the README)
is rendered from the same context keys, so the promise and the matrix cannot
drift apart.

Only majors are modelled. A stack whose dependency insists on a *point* release
of a major declares that major as its floor; if the dependency later raises the
floor again it raises the whole major, which is a change worth noticing.
"""

from __future__ import annotations

import re

from .registry import RegistryError, Stack

VERSION_RE = re.compile(r"^(?:1[4-9]|2[0-9])$")


def _rank(version: str) -> int:
    return int(version)


def supported(stack: Stack) -> tuple[str, ...]:
    """Majors this stack's template has been proven on (empty: not a Node stack)."""
    return stack.node_versions


def _floor(stack: Stack, requested: str | None, recorded: str | None) -> str | None:
    if not stack.node_versions:
        if requested:
            raise RegistryError(f"the {stack.name} stack has no --node choice")
        return None
    if requested and requested not in stack.node_versions:
        raise RegistryError(
            f"the {stack.name} stack supports Node "
            f"{', '.join(stack.node_versions)} (asked for {requested})"
        )
    floor = requested
    if floor is None and recorded in stack.node_versions:
        floor = recorded
    if floor is None:
        floor = stack.node_minimum
    if floor is None:  # pragma: no cover - registry validation prevents this
        return None
    if _rank(floor) < _rank(stack.node_minimum or floor):
        raise RegistryError(
            f"the {stack.name} stack needs Node {stack.node_minimum} or newer "
            f"(asked for {floor})"
        )
    return floor


def context(
    stack: Stack,
    requested: str | None = None,
    *,
    recorded: str | None = None,
) -> dict[str, str]:
    """The ``node_*`` render keys for *stack*."""
    floor = _floor(stack, requested, recorded)
    if floor is None:
        return {}
    versions = [version for version in stack.node_versions if _rank(version) >= _rank(floor)]
    return {
        "node_version": floor,
        "node_versions": ", ".join(f'"{version}"' for version in versions),
        "node_list": ", ".join(versions),
    }


def apply(
    stack: Stack,
    context_dict: dict,
    requested: str | None = None,
) -> dict:
    """Merge the keys into *context_dict*; raises when the request cannot be honoured."""
    keys = context(stack, requested, recorded=context_dict.get("node_version"))
    if not keys:
        context_dict.pop("node_version", None)
        context_dict.pop("node_versions", None)
        context_dict.pop("node_list", None)
        return context_dict
    context_dict.update(keys)
    return context_dict
