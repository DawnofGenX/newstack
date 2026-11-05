"""The three attacks, in order, and the defence each one defeats.

This module is part of the package on purpose: a rule nobody can demonstrate is a rule nobody
believes. `demo` runs it against throwaway databases and prints what each step proves.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canon import canonical
from .record import GENESIS, event_of
from .store import Store
from .verify import Checkpoint, checkpoint_of, verify


@dataclass(frozen=True, slots=True)
class Step:
    attack: str
    defence: str
    lines: list[str]
    caught: bool

    def render(self) -> list[str]:
        verdict = "caught" if self.caught else "MISSED"
        return [
            f"{self.attack:<30} {verdict:<7} {self.defence}",
            *(f"    {line}" for line in self.lines),
        ]


def _seed(path: Path, count: int = 3) -> Store:
    """A log with a few events and nothing interesting in it."""
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
    store = Store(path)
    for index in range(1, count + 1):
        store.append(actor="alice", action="note.update", target=f"note/{index}")
    return store


def edit_body(store: Store, seq: int, detail: dict[str, Any]) -> None:
    """Change what one row says, leaving its hash alone."""
    event = store.get(seq)
    if event is None:
        raise ValueError(f"no event at seq {seq}")
    body = dict(event.body)
    body["detail"] = detail
    store.raw().execute("UPDATE events SET body = ? WHERE seq = ?", (canonical(body), seq))


def delete_event(store: Store, seq: int) -> None:
    store.raw().execute("DELETE FROM events WHERE seq = ?", (seq,))


def rebuild_chain(store: Store) -> None:
    """Rewrite every body and recompute every hash — the attack a checksum cannot see.

    Anyone with write access to the file and a copy of this code can produce a chain that
    verifies perfectly. That is the whole reason a checkpoint has to be stored somewhere else.
    """
    seqs = [row["seq"] for row in store.raw().execute("SELECT seq FROM events ORDER BY seq")]
    previous = GENESIS
    for seq in seqs:
        event = store.get(seq)
        if event is None:
            raise ValueError(f"no event at seq {seq}")
        body = dict(event.body)
        body["prev_hash"] = previous
        body["detail"] = {**body["detail"], "note": "edited by whoever owns the file"}
        fresh = event_of(body)
        store.raw().execute(
            "UPDATE events SET body = ?, hash = ? WHERE seq = ?",
            (canonical(body), fresh.hash, body["seq"]),
        )
        previous = fresh.hash


def run(directory: Path) -> list[Step]:
    """Build a log three times, break it three ways, and report what noticed."""
    steps: list[Step] = []

    store = _seed(directory / "clean.db")
    try:
        report = verify(store)
        steps.append(
            Step(
                "nothing (a clean log)",
                "every link recomputes to its stored hash",
                report.lines(),
                caught=report.ok,
            )
        )
    finally:
        store.close()

    store = _seed(directory / "edited.db")
    try:
        edit_body(store, 2, {"note": "I was never here"})
        report = verify(store)
        steps.append(
            Step(
                "edit one row, keep its hash",
                "the body no longer hashes to the stored hash",
                report.lines(),
                caught=not report.ok,
            )
        )
    finally:
        store.close()

    store = _seed(directory / "deleted.db")
    try:
        delete_event(store, 2)
        report = verify(store)
        steps.append(
            Step(
                "delete a row",
                "the sequence numbers stop being contiguous",
                report.lines(),
                caught=not report.ok,
            )
        )
    finally:
        store.close()

    store = _seed(directory / "rebuilt.db")
    try:
        checkpoint: Checkpoint = checkpoint_of(store)
        rebuild_chain(store)
        chain_only = verify(store)
        steps.append(
            Step(
                "recompute every hash",
                "a chain is a checksum, so this looks clean",
                chain_only.lines(),
                caught=not chain_only.ok,
            )
        )
        guarded = verify(store, checkpoint)
        steps.append(
            Step(
                "recompute every hash, with a checkpoint",
                "the remembered head is the evidence",
                guarded.lines(),
                caught=not guarded.ok,
            )
        )
    finally:
        store.close()

    for name in ("clean.db", "edited.db", "deleted.db", "rebuilt.db"):
        with contextlib.suppress(OSError):
            (directory / name).unlink()
    return steps
