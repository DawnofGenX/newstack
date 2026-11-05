"""Six stories about resolution, each one a rule the code enforces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .index import Index, load
from .resolver import Resolution, ResolveError, resolve
from .versions import parse

BASE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "index.json"


@dataclass
class Story:
    title: str
    lines: list[str]


def _picked(resolution: Resolution) -> str:
    return ", ".join(
        f"{name} {resolution.version(name).text}" for name in sorted(resolution.choices)
    )


def stories(index: Index) -> list[Story]:
    out: list[Story] = []

    resolution = resolve(index, {"web": "^2.0.0", "cli": "^1.0.0"})
    out.append(
        Story(
            "the highest version is not always the answer",
            [
                "your project asks for web ^2.0.0 and cli ^1.0.0",
                "web 2.1.1 is the highest match, but it needs shared ^2.0.0",
                "cli needs shared ^1.0.0, so that branch is a dead end",
                f"the resolver walks back to web 2.0.0 and settles on: {_picked(resolution)}",
            ],
        )
    )

    try:
        resolve(index, {"web": "^2.1.0", "cli": "^1.0.0"})
        conflict = ["(unexpectedly resolved)"]
    except ResolveError as error:
        named = [item for item in error.conflicts if item.startswith("cannot pick")]
        conflict = [(named or error.conflicts or [str(error)])[0]]
    out.append(
        Story(
            "a conflict names the two ranges that cannot meet",
            [
                "your project asks for web ^2.1.0 and cli ^1.0.0",
                *conflict,
                "no version is printed, because printing the best-effort tree is how two "
                "installs of one project end up different",
            ],
        )
    )

    released = resolve(index, {"shared": "^2.0.0"})
    pre = resolve(index, {"shared": ">=3.0.0-rc.1"})
    out.append(
        Story(
            "prereleases are opt-in, never implied",
            [
                "3.0.0-rc.1 is published, but shared ^2.0.0 will not take it",
                f"  shared ^2.0.0      -> {released.version('shared').text}",
                f"  shared >=3.0.0-rc.1 -> {pre.version('shared').text}",
                "a range that never mentions a prerelease of that exact version has not "
                "agreed to run one",
            ],
        )
    )

    narrow = resolve(index, {"tiny": "^0.2.0"})
    out.append(
        Story(
            "a caret at major zero is not 'same major'",
            [
                "tiny publishes 0.2.3 and 0.3.0",
                f"  tiny ^0.2.0 -> {narrow.version('tiny').text}",
                "below 1.0.0 the leftmost non-zero part is the stable part, so ^0.2.0 stays "
                "on 0.2.x and 0.3.0 is a breaking release",
            ],
        )
    )

    roots = {"web": "^2.0.0", "cli": "^1.0.0"}
    first = resolve(index, {"cli": "^1.0.0", "web": "^2.0.0"})
    out.append(
        Story(
            "the answer does not depend on the order you wrote the roots",
            [
                f"roots in one order:  {_picked(first)}",
                f"roots in the other:  {_picked(resolve(index, roots))}",
                "pending packages are visited most-constrained first, and ties break on name",
            ],
        )
    )

    yesterday = {"web": parse("2.0.0"), "shared": parse("1.4.0")}
    kept = resolve(index, {"web": "^2.0.0"}, locked=yesterday)
    fresh = resolve(index, {"web": "^2.0.0"})
    out.append(
        Story(
            "a lock keeps the tree that worked",
            [
                f"with yesterday's lock: {_picked(kept)}",
                f"without a lock:       {_picked(fresh)}",
                "both satisfy ^2.0.0; the lock version is tried first because churn is a cost too",
                "an upgrade is a decision, so `check` reports drift only when the lock "
                "no longer resolves",
            ],
        )
    )
    return out


def render(stories_list: list[Story]) -> str:
    lines: list[str] = []
    for number, story in enumerate(stories_list, start=1):
        lines.append(f"{number}. {story.title}")
        lines.extend(f"   {line}" for line in story.lines)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    index = load(BASE)
    print(render(stories(index)))
    return 0
