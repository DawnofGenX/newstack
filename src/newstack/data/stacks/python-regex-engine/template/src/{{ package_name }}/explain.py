"""Every step of the simulation, printed as the set it actually is.

A reader who sees one state per step is looking at a different machine from the
one that runs. The trace below prints the set, so "the pattern would have to guess
here" becomes a set with two members in it.
"""

from __future__ import annotations

from . import nfa as nfa_module
from . import syntax


def _set_text(states: frozenset[int]) -> str:
    if not states:
        return "{}"
    return "{" + ", ".join(str(state) for state in sorted(states)) + "}"


def trace_lines(node: syntax.Node, text: str, *, limit: int = 40) -> list[str]:
    machine = nfa_module.compile_node(node, node.render())
    sets = machine.run(text)
    lines = [
        f"pattern    {node.render()}",
        f"text       {text!r}",
        f"steps      {len(text)} character(s), {machine.states} state(s) in the machine",
        "",
        "   at  seen        states                          accepting",
    ]
    shown = text[:limit]
    for index, states in enumerate(sets[: len(shown) + 1]):
        seen = "'" + (shown[index - 1] if index else "") + "'" if index else "-"
        mark = "yes" if machine.accepts(states) else "no"
        lines.append(f"  {index:>3}  {seen:<10}  {_set_text(states):<30}  {mark}")
    if len(text) > limit:
        lines.append(f"  ...  {len(text) - limit} more character(s) not printed")
    return lines


def verdict_lines(node: syntax.Node, text: str) -> list[str]:
    machine = nfa_module.compile_node(node, node.render())
    sets = machine.run(text)
    final = sets[-1]
    lines = [f"pattern    {node.render()}", f"text       {text!r}"]
    if machine.accepts(final):
        lines.append("verdict    the whole text matches")
    elif machine.dead_end(final):
        lines.append("verdict    no match, and the machine has no state left to be in")
    else:
        lines.append("verdict    no match, because no accepting state survived")
    longest = machine.accepts_prefix(text)
    if longest is None:
        lines.append("prefix     no prefix of this text is accepted")
    else:
        lines.append(f"prefix     the longest accepted prefix is {longest} character(s)")
    if len(final) > 1:
        lines.append(
            f"note       the last step was carrying {len(final)} state(s) at once, "
            "which is the set a backtracking engine would have to try one by one"
        )
    return lines


def machine_lines(node: syntax.Node) -> list[str]:
    machine = nfa_module.compile_node(node, node.render())
    lines = [f"pattern    {node.render()}", *machine.lines()]
    table = machine.outgoing()
    for state in range(machine.states):
        outs = table.get(state, [])
        if not outs:
            lines.append(f"  state {state:<3} (no way out)")
            continue
        described = ", ".join(
            f"{label.text() if label is not None else 'eps'}->{target}" for label, target in outs
        )
        lines.append(f"  state {state:<3} {described}")
    return lines
