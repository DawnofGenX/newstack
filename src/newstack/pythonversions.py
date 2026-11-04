"""The Python version a generated project declares.

A stack that works on more than one interpreter says so in ``stack.json``::

    "python": {"minimum": "3.10", "versions": ["3.10", "3.11", "3.12", "3.13"]}

``--python`` moves the floor up — never below the stack's own minimum — and the
template renders everything that depends on it (``requires-python``, the ruff
target, the classifier list, the CI matrix, the Docker base image) from the same
four context keys. That is the point: the promise in ``pyproject.toml`` and the
versions CI runs cannot drift apart, because one value writes both.
"""

from __future__ import annotations

import re

from .registry import RegistryError, Stack

VERSION_RE = re.compile(r"^3\.(?:[89]|1[0-9])$")


def _rank(version: str) -> tuple[int, int]:
    major, minor = version.split(".")
    return int(major), int(minor)


def supported(stack: Stack) -> tuple[str, ...]:
    """Versions this stack's template has been proven on (empty: not a Python stack)."""
    return stack.python_versions


def _floor(stack: Stack, requested: str | None, recorded: str | None) -> str | None:
    if not stack.python_versions:
        if requested:
            raise RegistryError(f"the {stack.name} stack has no --python choice")
        return None
    if requested and requested not in stack.python_versions:
        raise RegistryError(
            f"the {stack.name} stack supports Python "
            f"{', '.join(stack.python_versions)} (asked for {requested})"
        )
    floor = requested
    if floor is None and recorded in stack.python_versions:
        floor = recorded
    if floor is None:
        floor = stack.python_minimum
    if floor is None:  # pragma: no cover - registry validation prevents this
        return None
    if _rank(floor) < _rank(stack.python_minimum or floor):
        raise RegistryError(
            f"the {stack.name} stack needs Python {stack.python_minimum} or newer "
            f"(asked for {floor})"
        )
    return floor


def context(
    stack: Stack,
    requested: str | None = None,
    *,
    recorded: str | None = None,
) -> dict[str, str]:
    """The ``python_*`` render keys for *stack*.

    ``recorded`` is the floor a project was generated with, so ``newstack update``
    keeps writing the version the project actually declares unless asked otherwise.
    """
    floor = _floor(stack, requested, recorded)
    if floor is None:
        return {}
    versions = [version for version in stack.python_versions if _rank(version) >= _rank(floor)]
    classifiers = [f'    "Programming Language :: Python :: {version}"' for version in versions]
    return {
        "python_version": floor,
        "python_tag": floor.replace(".", ""),
        "python_versions": ", ".join(f'"{version}"' for version in versions),
        "python_classifiers": ",\n".join(classifiers),
    }


def apply(
    stack: Stack,
    context_dict: dict,
    requested: str | None = None,
) -> dict:
    """Merge the keys into *context_dict*; raises when the request cannot be honoured."""
    keys = context(stack, requested, recorded=context_dict.get("python_version"))
    if not keys:
        context_dict.pop("python_version", None)
        context_dict.pop("python_tag", None)
        context_dict.pop("python_versions", None)
        context_dict.pop("python_classifiers", None)
        return context_dict
    context_dict.update(keys)
    return context_dict
