"""RFC 6901 JSON Pointers.

A pointer is a string, and every character in it is either a separator, an
escape, or data. The two ways to get this wrong are to split on "/" without
unescaping (so a key that genuinely contains a slash becomes two keys) and to
treat a segment that looks like a number as an index even when the target is an
object (so {"0": "x"} is unreachable).
"""

from __future__ import annotations

from typing import Any

ESCAPES = (("~", "~0"), ("/", "~1"))


class PointerError(ValueError):
    """The pointer is not a pointer, or it does not name anything."""


def escape(token: str) -> str:
    """Turn a key into one pointer segment."""
    return token.replace("~", "~0").replace("/", "~1")


def unescape(token: str) -> str:
    """Turn one pointer segment back into a key."""
    out = []
    index = 0
    while index < len(token):
        character = token[index]
        if character != "~":
            out.append(character)
            index += 1
            continue
        following = token[index + 1 : index + 2]
        if following == "0":
            out.append("~")
        elif following == "1":
            out.append("/")
        else:
            raise PointerError(
                f"invalid escape '~{following}' in '{token}': only ~0 and ~1 are defined, "
                "so this segment cannot be unescaped without guessing"
            )
        index += 2
    return "".join(out)


def parse(text: str) -> tuple[str, ...]:
    """Split a pointer into unescaped segments. "" is the whole document."""
    if not isinstance(text, str):
        raise PointerError(f"a pointer is a string, not {type(text).__name__}")
    if text == "":
        return ()
    if not text.startswith("/"):
        raise PointerError(
            f"'{text}' is not a pointer: the whole document is the empty string, "
            "and every other pointer starts with '/'"
        )
    return tuple(unescape(segment) for segment in text[1:].split("/"))


def render(parts: tuple[str, ...] | list[str]) -> str:
    """Build a pointer from segments."""
    return "".join(f"/{escape(part)}" for part in parts)


def index_of(token: str, length: int) -> int:
    """Read an array index, refusing everything JSON does not define."""
    if token == "-":
        raise PointerError(
            "'-' names the position after the last element, so it has no value to read"
        )
    if not token.isdigit():
        raise PointerError(f"'{token}' is not an array index: indices are decimal digits")
    if token != "0" and token.startswith("0"):
        raise PointerError(f"'{token}' is not an array index: a leading zero is not allowed")
    number = int(token)
    if number >= length:
        raise PointerError(f"index {number} is past the end of a list of length {length}")
    return number


def resolve(document: Any, pointer: str | tuple[str, ...]) -> Any:
    """Walk the pointer and return what it names."""
    parts = parse(pointer) if isinstance(pointer, str) else pointer
    current = document
    for depth, token in enumerate(parts):
        where = render(parts[: depth + 1])
        if isinstance(current, dict):
            if token not in current:
                raise PointerError(f"'{where}' names nothing: this object has no key {token!r}")
            current = current[token]
        elif isinstance(current, list):
            current = current[index_of(token, len(current))]
        else:
            raise PointerError(
                f"'{where}' names nothing: '{render(parts[:depth]) or ''}' is a "
                f"{type(current).__name__}, which has no children"
            )
    return current


def parent_of(document: Any, parts: tuple[str, ...]) -> tuple[Any, str]:
    """Return the container that holds the last segment, and that segment.

    The root has no parent, so patching it is a whole-document replacement and
    the caller has to handle that case before asking.
    """
    if not parts:
        raise PointerError("the root pointer has no parent to patch")
    return resolve(document, parts[:-1]), parts[-1]
