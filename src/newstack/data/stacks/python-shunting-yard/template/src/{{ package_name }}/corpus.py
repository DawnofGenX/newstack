"""Expressions in, audits out: corpora, generators, snapshots.

One record per line - ``infix | postfix | value`` - and blank
lines and # comments are skipped. The generator is deterministic
from its seed, so a seeded corpus answers the same way forever,
and audit recomputes every field of every record through the
yard, the reckoning, and the oracle. Where the three disagree,
the record is broken and audit names it.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path as DiskPath

from .calc import evaluate, value_of
from .expr import ExprError
from .oracle import descent
from .yard import postfix_text, to_postfix

DEFAULT_SEED = 20261107


class CorpusError(ValueError):
    """A corpus cannot be read, written, generated, or replayed."""

    __slots__ = ()


@dataclass(frozen=True)
class Record:
    """One expression, the postfix the yard owes it, its value."""

    expr: str
    postfix: str
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.expr, str) or not self.expr.strip():
            raise CorpusError(f"{self.expr!r} is no expression")
        if not isinstance(self.postfix, str) or not self.postfix.strip():
            raise CorpusError(f"{self.postfix!r} is no postfix text")
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise CorpusError(f"{self.value!r} is no value")


@dataclass(frozen=True)
class Snapshot:
    """A frozen corpus and the seed that owes it."""

    exprs: tuple
    seed: int

    def dumps(self) -> str:
        return json.dumps({"seed": self.seed, "exprs": list(self.exprs)})

    @classmethod
    def loads(cls, payload: str) -> Snapshot:
        try:
            record = json.loads(payload)
            return cls(tuple(record["exprs"]), int(record["seed"]))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as failure:
            raise CorpusError(f"half a snapshot: {failure}") from failure


def audit(record: object) -> list:
    """Recompute a record through yard, reckoning, oracle; name breaks."""
    if not isinstance(record, Record):
        raise CorpusError(f"{record!r} is no record")
    breaks: list = []
    try:
        owed = postfix_text(to_postfix(record.expr))
    except ExprError as failure:
        return [f"{record.expr!r}: the yard refused it: {failure}"]
    if owed != record.postfix:
        breaks.append(f"{record.expr!r}: yard answers {owed!r}, ledger says {record.postfix!r}")
    try:
        if evaluate(to_postfix(record.expr)) != record.value:
            breaks.append(f"{record.expr!r}: the yard answers {record.value}, not reckoned")
    except ExprError as failure:
        breaks.append(f"{record.expr!r}: the reckoning refused it: {failure}")
    try:
        if descent(record.expr) != record.value:
            breaks.append(f"{record.expr!r}: the oracle answers elsewhere")
    except ExprError as failure:
        breaks.append(f"{record.expr!r}: the oracle refused it: {failure}")
    return breaks


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list:
    """A deterministic list of infix expressions and their answers."""
    if count <= 0:
        raise CorpusError(f"no records from {count}")
    rng = random.Random(seed)
    records: list = []
    seen: set = set()
    while len(records) < count:
        terms = [str(rng.randint(0, 30))]
        for _step in range(rng.randint(1, 4)):
            terms.append(rng.choice("+-*"))
            terms.append(str(rng.randint(1, 12)))
            if rng.random() < 0.2:
                terms.append("/")
                terms.append(str(rng.randint(1, 9)))
        expr = " ".join(terms)
        if rng.random() < 0.3:
            expr = f"({expr}) + {rng.randint(1, 9)}"
        if expr in seen:
            continue
        try:
            answer = value_of(expr)
            descent(expr)
        except ExprError:
            continue
        seen.add(expr)
        records.append(Record(expr, postfix_text(to_postfix(expr)), answer))
    return records


def load_records(path: str) -> list:
    """One record per line; blank lines and # comments skipped."""
    try:
        text = DiskPath(path).read_text(encoding="utf-8")
    except OSError as failure:
        raise CorpusError(f"no such corpus: {path}") from failure
    records: list = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = [field.strip() for field in stripped.split("|")]
        if len(fields) != 3:
            raise CorpusError(f"the ledger holds {stripped!r}, not a record")
        try:
            records.append(Record(fields[0], fields[1], int(fields[2])))
        except (CorpusError, ValueError) as failure:
            raise CorpusError(f"the ledger row {stripped!r} is unreadable: {failure}") from failure
    if not records:
        raise CorpusError(f"{path} names no records")
    return records


def write_records(records: list, path: str) -> None:
    """Write a ledger, one record per line, ended by a newline."""
    try:
        rows = [f"{r.expr} | {r.postfix} | {r.value}" for r in records]
        DiskPath(path).write_text("\n".join(rows) + "\n", encoding="utf-8")
    except OSError as failure:
        raise CorpusError(f"cannot write {path}: {failure}") from failure


def report_lines(records: list) -> list:
    """Audit the ledger and answer line by line, answer vs oracle."""
    lines: list = []
    for record in records:
        breaks = audit(record)
        mark = "quiet" if not breaks else "BROKE"
        lines.append(f"{record.expr} = {record.value} [{mark}] {record.postfix}")
    return lines
