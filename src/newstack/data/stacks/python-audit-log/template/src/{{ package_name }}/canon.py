"""Canonical bytes: what gets hashed, and why the hash must not depend on the encoder.

A digest is only useful if two programs computing it agree. `json.dumps` has five knobs that change
the bytes without changing the value — key order, separators, `ensure_ascii`, the encoding it is
written with, and whether floats print as `1.0` or `1`. Pin all of them here, once.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

ENCODING = "utf-8"


class CanonError(ValueError):
    """The value cannot be canonicalised, so it cannot be hashed reproducibly."""


def check_json(value: Any, path: str = "$") -> None:
    """Refuse the values that hash differently in different runtimes."""
    if value is None or isinstance(value, bool | int):
        return
    if isinstance(value, float):
        raise CanonError(
            f'{path} is a float: 1.0 prints as "1.0" in Python and "1" in JavaScript, so two '
            "verifiers would disagree about the same event. Store the minor units as an int, or "
            "the ratio as a string"
        )
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            check_json(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonError(
                    f"{path} has a non-string key {key!r}; JSON object keys are strings"
                )
            check_json(item, f"{path}.{key}")
        return
    raise CanonError(f"{path} is a {type(value).__name__}, which JSON cannot represent")


def canonical(value: Any) -> str:
    """One line of JSON, keys sorted, no incidental whitespace, non-ASCII kept as UTF-8."""
    check_json(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    """The SHA-256 of the canonical form, as lowercase hex."""
    return hashlib.sha256(canonical(value).encode(ENCODING)).hexdigest()
