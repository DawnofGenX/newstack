"""RFC 6902 JSON Patch, applied atomically.

Every operation is applied to a copy, and the copy is thrown away if any
operation fails. A patch that half-applied would be worse than one that failed:
the caller would have to know which half.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from .pointer import PointerError, index_of, parse, render, resolve

OPERATIONS = ("add", "copy", "move", "remove", "replace", "test")


class PatchError(RuntimeError):
    """The patch is not a patch, or it does not apply."""


class TestFailed(PatchError):
    """A test operation compared unequal, so the patch refused to run."""


def equal(left: Any, right: Any) -> bool:
    """JSON equality: numbers compare by value, booleans are not numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            equal(a, b) for a, b in zip(left, right, strict=False)
        )
    return type(left) is type(right) and left == right


def _insert_index(token: str, length: int) -> int:
    """An index for add: the end of the list is a legal position."""
    if token == "-":
        return length
    if not token.isdigit():
        raise PatchError(f"'{token}' is not an array index: indices are decimal digits, or '-'")
    if token != "0" and token.startswith("0"):
        raise PatchError(f"'{token}' is not an array index: a leading zero is not allowed")
    number = int(token)
    if number > length:
        raise PatchError(f"index {number} is past the end of a list of length {length}")
    return number


def _add(document: Any, parts: tuple[str, ...], value: Any) -> Any:
    if not parts:
        return copy.deepcopy(value)
    holder, token = resolve(document, parts[:-1]), parts[-1]
    if isinstance(holder, dict):
        holder[token] = copy.deepcopy(value)
        return document
    if isinstance(holder, list):
        holder.insert(_insert_index(token, len(holder)), copy.deepcopy(value))
        return document
    raise PatchError(
        f"cannot add to '{render(parts[:-1]) or '(root)'}': it is a "
        f"{type(holder).__name__}, which has no members"
    )


def _remove(document: Any, parts: tuple[str, ...]) -> Any:
    if not parts:
        raise PatchError(
            "the root cannot be removed: a document has to be something, so replace it instead"
        )
    holder, token = resolve(document, parts[:-1]), parts[-1]
    if isinstance(holder, dict):
        if token not in holder:
            raise PatchError(f"cannot remove '{render(parts)}': this object has no key {token!r}")
        del holder[token]
        return document
    if isinstance(holder, list):
        del holder[index_of(token, len(holder))]
        return document
    raise PatchError(
        f"cannot remove from '{render(parts[:-1]) or '(root)'}': it is a "
        f"{type(holder).__name__}, which has no members"
    )


def _replace(document: Any, parts: tuple[str, ...], value: Any) -> Any:
    if not parts:
        return copy.deepcopy(value)
    resolve(document, parts)  # the target must already exist
    holder, token = resolve(document, parts[:-1]), parts[-1]
    if isinstance(holder, dict):
        holder[token] = copy.deepcopy(value)
    else:
        holder[index_of(token, len(holder))] = copy.deepcopy(value)
    return document


def _operand(operation: dict, key: str, index: int) -> Any:
    if key not in operation:
        raise PatchError(f"operation {index + 1} is a '{operation['op']}' without a '{key}' member")
    return operation[key]


def _one(document: Any, operation: Any, index: int) -> Any:
    if not isinstance(operation, dict):
        raise PatchError(
            f"operation {index + 1} is a {type(operation).__name__}, not an object "
            "with an op and a path"
        )
    name = operation.get("op")
    if name not in OPERATIONS:
        raise PatchError(
            f"operation {index + 1} names '{name}', which is not an operation: "
            f"the RFC defines {', '.join(OPERATIONS)}"
        )
    try:
        parts = parse(_operand(operation, "path", index))
        if name == "add":
            return _add(document, parts, _operand(operation, "value", index))
        if name == "remove":
            return _remove(document, parts)
        if name == "replace":
            return _replace(document, parts, _operand(operation, "value", index))
        if name == "move":
            source_parts = parse(_operand(operation, "from", index))
            if source_parts == parts:
                return document
            if parts[: len(source_parts)] == source_parts:
                raise PatchError(
                    f"cannot move '{render(source_parts)}' into its own child "
                    f"'{render(parts)}': the value would contain itself"
                )
            value = resolve(document, source_parts)
            document = _remove(document, source_parts)
            return _add(document, parts, value)
        if name == "copy":
            source_parts = parse(_operand(operation, "from", index))
            return _add(document, parts, resolve(document, source_parts))
        current = resolve(document, parts)
        expected = _operand(operation, "value", index)
        if not equal(current, expected):
            raise TestFailed(
                f"test failed at '{render(parts) or '(root)'}': the document holds "
                f"{json.dumps(current)} and the patch expected {json.dumps(expected)}"
            )
        return document
    except PointerError as error:
        raise PatchError(str(error)) from error


def apply(document: Any, operations: list[dict]) -> Any:
    """Apply every operation or none of them, and never mutate the argument."""
    if isinstance(operations, dict):
        raise PatchError("a patch is a list of operations, not a single object")
    working = copy.deepcopy(document)
    for index, operation in enumerate(operations):
        try:
            working = _one(working, operation, index)
        except PatchError as error:
            name = operation.get("op") if isinstance(operation, dict) else "operation"
            raise type(error)(
                f"operation {index + 1} ({name}) failed, so nothing was applied: {error}"
            ) from error
    return working


def check(document: Any, operations: list[dict]) -> None:
    """Apply and discard, which is what a dry run is."""
    apply(document, operations)


def load(path) -> list[dict]:
    """Read a patch file: one JSON array of operations."""
    text = path.read_text()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise PatchError(f"{path} is not JSON: {error}") from error
    if not isinstance(payload, list):
        raise PatchError(
            f"{path} holds a {type(payload).__name__}; a patch is a list of operations"
        )
    return payload
