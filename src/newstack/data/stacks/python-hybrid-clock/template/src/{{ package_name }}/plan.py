"""Read a plan of events from a file, so a scenario is data and not a script."""

from __future__ import annotations

import json
from pathlib import Path

from .world import World, WorldError

CHUNK = 1


class PlanError(ValueError):
    """A plan that cannot be carried out, before any of it is carried out."""


def load(path: Path) -> list[dict]:
    """Read JSONL, refusing a line that is not an object with a known type."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise PlanError(f"cannot read {path}: {error}") from error
    events: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise PlanError(f"{path}:{number} is not JSON: {error.msg}") from error
        if not isinstance(event, dict):
            raise PlanError(f"{path}:{number} is not an object")
        if event.get("type") not in KINDS:
            raise PlanError(
                f"{path}:{number} has type {event.get('type')!r}; "
                f"the plan can do {', '.join(sorted(KINDS))}"
            )
        events.append(event)
    if not events:
        raise PlanError(f"{path} holds no events; an empty plan proves nothing")
    return events


KINDS = ("back", "local", "offset", "send", "tick")


def execute(events: list[dict], *, start_ms: int, max_skew_ms: int | None = None) -> World:
    """Run the plan and hand back the world it produced."""
    nodes: dict[str, int] = {}
    for event in events:
        if event["type"] == "offset":
            nodes[str(event["node"])] = int(event["ms"])
    if not nodes:
        nodes = {"a": 0}
    world = World(nodes, start_ms=start_ms, max_skew_ms=max_skew_ms)
    for number, event in enumerate(events, start=1):
        try:
            _apply(world, event)
        except (WorldError, KeyError, ValueError) as error:
            raise PlanError(f"event {number} ({event['type']}) failed: {error}") from error
    return world


def _apply(world: World, event: dict) -> None:
    kind = event["type"]
    if kind == "offset":
        return
    if kind == "tick":
        world.tick(int(event.get("ms", 1)))
    elif kind == "back":
        world.step_back(str(event["node"]), int(event.get("ms", 1)))
    elif kind == "local":
        world.local(str(event["node"]), str(event.get("detail", "")))
    elif kind == "send":
        world.send(str(event["from"]), str(event["to"]), str(event.get("detail", "")))
    else:  # pragma: no cover - load() has already refused anything else
        raise PlanError(f"cannot apply {kind}")
