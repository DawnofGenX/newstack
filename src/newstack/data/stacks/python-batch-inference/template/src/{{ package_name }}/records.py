"""JSONL request and result records.

Requests are strict: a bad line is an error naming the file and line, because a
silently skipped request is a silently smaller run.  Results are append-only and
tolerate a torn final line, because the process that wrote them may have been
killed mid-write — that is the whole reason this tool is resumable.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


class RecordError(ValueError):
    """A request or result line could not be read."""


@dataclass(frozen=True)
class Request:
    """One prompt to send."""

    id: str
    prompt: str


@dataclass(frozen=True)
class Result:
    """One answer, or the reason there is none."""

    id: str
    output: str = ""
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    attempts: int = 0
    ok: bool = True
    error: str = ""

    def line(self) -> str:
        """The JSON line written to the results file."""
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_line(cls, line: str) -> Result:
        """Parse a line written by :meth:`line`."""
        data = json.loads(line)
        known = {name: data[name] for name in cls.__dataclass_fields__ if name in data}
        return cls(**known)


def _numbered(lines: Iterable[str], source: str) -> Iterator[tuple[int, str]]:
    for number, line in enumerate(lines, start=1):
        if line.strip():
            yield number, line


def _object(line: str, where: str) -> dict:
    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise RecordError(f"{where}: not JSON ({exc.msg})") from exc
    if not isinstance(data, dict):
        raise RecordError(f"{where}: expected a JSON object, got {type(data).__name__}")
    return data


def parse_requests(lines: Iterable[str], source: str = "<stdin>") -> list[Request]:
    """Parse request lines, rejecting duplicates instead of guessing which one wins."""
    requests: list[Request] = []
    seen: dict[str, int] = {}
    for number, line in _numbered(lines, source):
        where = f"{source}:{number}"
        data = _object(line, where)
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise RecordError(f"{where}: missing a non-empty string id")
        if identifier in seen:
            raise RecordError(
                f"{where}: duplicate id {identifier!r}, first seen on line {seen[identifier]}"
            )
        seen[identifier] = number
        prompt = data.get("prompt")
        if not isinstance(prompt, str):
            raise RecordError(f"{where}: id {identifier!r} has no string prompt")
        requests.append(Request(id=identifier, prompt=prompt))
    if not requests:
        raise RecordError(f"{source}: no requests")
    return requests


def load_requests(path: str | Path) -> list[Request]:
    """Read request records from ``path``."""
    try:
        with open(path, encoding="utf-8") as handle:
            return parse_requests(handle, str(path))
    except OSError as exc:
        raise RecordError(f"{path}: cannot read ({exc.strerror})") from exc


def parse_results(lines: Iterable[str], source: str = "<results>") -> dict[str, Result]:
    """Parse result lines into a map, so a rerun can skip what is already done.

    A torn *final* line is discarded rather than raised on: it is the signature of
    a process killed mid-write, and the point of this tool is to resume from there.
    """
    rows = list(_numbered(lines, source))
    done: dict[str, Result] = {}
    for index, (number, line) in enumerate(rows):
        where = f"{source}:{number}"
        try:
            result = Result.from_line(line)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            if index == len(rows) - 1:
                continue
            raise RecordError(f"{where}: unreadable result ({exc})") from exc
        done[result.id] = result
    return done


def load_results(path: str | Path) -> dict[str, Result]:
    """Read what a previous run already wrote."""
    try:
        with open(path, encoding="utf-8") as handle:
            return parse_results(handle, str(path))
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise RecordError(f"{path}: cannot read ({exc.strerror})") from exc


class ResultWriter:
    """Append results, flushing every line so a crash loses at most one request."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: TextIO = self.path.open("a", encoding="utf-8")

    def write(self, result: Result) -> None:
        """Append one result and flush it."""
        self._handle.write(result.line() + "\n")
        self._handle.flush()

    def close(self) -> None:
        """Close the file."""
        self._handle.close()

    def __enter__(self) -> ResultWriter:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
