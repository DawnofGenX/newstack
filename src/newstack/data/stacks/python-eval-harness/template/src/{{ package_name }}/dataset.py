"""Reading the two JSONL files an evaluation needs.

Both loaders fail loudly and say which line is wrong: a harness that skips a
malformed row and reports a score anyway is worse than one that stops.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


class DatasetError(Exception):
    """A file could not be read as examples or predictions."""


@dataclass(frozen=True)
class Example:
    id: str
    prompt: str
    gold: str


def _rows(lines: Iterable[str], source: str) -> Iterable[tuple[int, dict]]:
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"{source}:{number}: not JSON: {exc.msg}") from None
        if not isinstance(row, dict):
            kind = type(row).__name__
            raise DatasetError(f"{source}:{number}: expected a JSON object, got {kind}")
        yield number, row


def _member(row: dict, key: str, number: int, source: str) -> str:
    try:
        value = row[key]
    except KeyError:
        raise DatasetError(f"{source}:{number}: missing {key!r}") from None
    if not isinstance(value, str):
        kind = type(value).__name__
        raise DatasetError(f"{source}:{number}: {key!r} must be a string, got {kind}")
    return value


def _example(row: dict, number: int, source: str) -> Example:
    example = Example(
        id=_member(row, "id", number, source),
        prompt=_member(row, "prompt", number, source),
        gold=_member(row, "gold", number, source),
    )
    if not example.id.strip():
        raise DatasetError(f"{source}:{number}: 'id' is empty")
    return example


def load_examples(path: str | Path) -> list[Example]:
    """Read ``{"id": ..., "prompt": ..., "gold": ...}`` rows, keeping file order."""

    source = str(path)
    try:
        with open(path, encoding="utf-8") as handle:
            pairs = [
                (number, _example(row, number, source)) for number, row in _rows(handle, source)
            ]
    except OSError as exc:
        raise DatasetError(f"{source}: cannot read: {exc.strerror}") from None
    if not pairs:
        raise DatasetError(f"{source}: no examples")

    examples: list[Example] = []
    seen: set[str] = set()
    for number, example in pairs:
        # Duplicate ids would be counted twice and silently reweight the set.
        if example.id in seen:
            raise DatasetError(f"{source}:{number}: duplicate id {example.id!r}")
        seen.add(example.id)
        examples.append(example)
    return examples


def parse_predictions(lines: Iterable[str], source: str = "<stdin>") -> dict[str, str]:
    """Parse prediction rows from any iterable of text lines."""

    predictions: dict[str, str] = {}
    for number, row in _rows(lines, source):
        key = _member(row, "id", number, source)
        if key in predictions:
            raise DatasetError(f"{source}:{number}: duplicate id {key!r}")
        predictions[key] = _member(row, "prediction", number, source)
    return predictions


def load_predictions(path: str | Path) -> dict[str, str]:
    """Read ``{"id": ..., "prediction": ...}`` rows from a file."""

    source = str(path)
    try:
        with open(path, encoding="utf-8") as handle:
            return parse_predictions(handle, source)
    except OSError as exc:
        raise DatasetError(f"{source}: cannot read: {exc.strerror}") from None
