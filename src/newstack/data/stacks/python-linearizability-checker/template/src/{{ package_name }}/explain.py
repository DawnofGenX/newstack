"""The verdict, the witness order, and the smallest core that fails."""

from __future__ import annotations

from .check import Outcome, is_minimal, shrink
from .history import History


def witness_lines(history: History, outcome: Outcome) -> list[str]:
    lines: list[str] = []
    for position, index in enumerate(outcome.order, start=1):
        op = history.operations[index]
        lines.append(f"{position:>3}  {op.text()}")
    return lines


def verdict_lines(history: History, outcome: Outcome) -> list[str]:
    lines = [f"verdict    {outcome.verdict}", f"reason     {outcome.reason}"]
    lines.append(
        f"search     {outcome.nodes} node(s), {outcome.memo_hits} memo hit(s), "
        f"{len(history)} operation(s)"
    )
    if outcome.linearizable:
        lines.append("witness    one order that holds:")
        lines.extend(witness_lines(history, outcome))
        return lines
    core, _verdict = shrink(history)
    minimal = is_minimal(core)
    lines.append(
        f"core       {len(core)} of {len(history)} operation(s)"
        + (", and removing any one of them makes the rest linearizable" if minimal else "")
    )
    lines.extend(f"  {op.text()}" for op in core.operations)
    return lines


def account_lines(history: History) -> list[str]:
    """What each client did, in its own order, before any verdict is given."""
    lines: list[str] = []
    for client in history.clients:
        operations = history.of_client(client)
        lines.append(f"client {client}  {len(operations)} operation(s)")
        lines.extend(f"  {op.text()}" for op in operations)
    return lines
