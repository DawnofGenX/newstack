"""Six stories about pointers and patches, each one checkable.

Every story ends with a claim; the claim is computed, not written by hand, so a
regression in the code turns the story into a failure instead of a lie.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .diff import diff
from .patch import PatchError, apply, equal
from .pointer import PointerError, render, resolve

BASE = Path(__file__).resolve().parent.parent.parent / "fixtures"


@dataclass(frozen=True)
class Story:
    title: str
    lines: tuple[str, ...]
    held: bool


def _dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def escaping_story() -> Story:
    document = {"a/b": 1, "m~n": 2}
    found = resolve(document, "/a~1b")
    rendered = render(("m~n",))
    naive: Any = document
    missing = False
    try:
        for token in ["", "a", "b"][1:]:
            naive = naive[token]
    except KeyError:
        missing = True
    lines = (
        f"document        {_dump(document)}",
        f"pointer /a~1b   resolves to {found}",
        f"key 'm~n'       renders as {rendered}",
        "a splitter that ignores the escapes walks key 'a' then key 'b' and finds nothing: "
        f"{missing}",
    )
    return Story("1. a key that holds a slash is not two keys", lines,
                 found == 1 and rendered == "/m~0n" and missing)


def numeric_key_story() -> Story:
    object_document = {"0": "an object key"}
    list_document = ["the first element"]
    from_object = resolve(object_document, "/0")
    from_list = resolve(list_document, "/0")
    refusals = []
    for pointer in ("/01", "/-"):
        try:
            resolve(list_document, pointer)
        except PointerError as error:
            refusals.append(f"{pointer}: {error}")
    lines = (
        f"the same pointer on an object: {_dump(from_object)}",
        f"the same pointer on a list:   {_dump(from_list)}",
        *(f"refused {line}" for line in refusals),
    )
    return Story("2. a numeric key is not an index", lines,
                 from_object == "an object key" and from_list == "the first element"
                 and len(refusals) == 2)


def shifting_story() -> Story:
    document = {"items": ["a", "c"]}
    inserted = apply(document, [{"op": "add", "path": "/items/1", "value": "b"}])
    removed = apply(inserted, [{"op": "remove", "path": "/items/0"}])
    appended = apply(removed, [{"op": "add", "path": "/items/-", "value": "d"}])
    lines = (
        f"start           {_dump(document)}",
        f"add /items/1 b  {_dump(inserted)}",
        f"remove /items/0 {_dump(removed)}",
        f"add /items/- d  {_dump(appended)}",
        "indices are positions, not identities: the element that was at 1 is now at 0",
    )
    return Story("3. add inserts and remove shifts", lines,
                 inserted["items"] == ["a", "b", "c"] and removed["items"] == ["b", "c"]
                 and appended["items"] == ["b", "c", "d"])


def condition_story() -> Story:
    document = {"version": 2, "value": "old"}
    patch = [{"op": "test", "path": "/version", "value": 3},
             {"op": "replace", "path": "/value", "value": "new"}]
    try:
        apply(document, patch)
    except PatchError as error:
        message = str(error)
    else:
        message = "the patch applied, which it should not have"
    lines = (
        f"document        {_dump(document)}",
        "patch           test /version == 3, then replace /value",
        f"refused         {message}",
        f"document after  {_dump(document)}",
    )
    return Story("4. the test operation is the condition", lines,
                 equal(document, {"version": 2, "value": "old"}) and "test failed" in message)


def atomic_story() -> Story:
    document = {"a": 1}
    patch = [
        {"op": "add", "path": "/b", "value": 2},
        {"op": "replace", "path": "/missing", "value": 3},
        {"op": "add", "path": "/c", "value": 4},
    ]
    try:
        apply(document, patch)
    except PatchError as error:
        message = str(error)
    else:
        message = "the patch applied, which it should not have"
    lines = (
        f"document        {_dump(document)}",
        f"refused         {message}",
        f"document after  {_dump(document)}",
        "the first operation was rolled back with the third: 'b' is absent too",
    )
    return Story("5. a patch applies whole or not at all", lines,
                 equal(document, {"a": 1}) and "nothing was applied" in message)


def diff_story() -> Story:
    before = json.loads((BASE / "document.json").read_text())
    after = json.loads((BASE / "after.json").read_text())
    operations = diff(before, after)
    rebuilt = apply(before, operations)
    numeric = apply({"n": 1}, [{"op": "test", "path": "/n", "value": 1.0}])
    lines = (
        f"operations      {len(operations)}",
        f"apply(diff)     {_dump(rebuilt)}",
        f"equal to after  {equal(rebuilt, after)}",
        f"1 and 1.0       the test passes, so the document is {_dump(numeric)}",
        "the diff was not written by hand: it was computed, applied and compared",
    )
    return Story("6. a diff proves itself by applying", lines,
                 equal(rebuilt, after) and len(operations) > 0
                 and equal(numeric, {"n": 1}))


def stories() -> list[Story]:
    return [
        escaping_story(),
        numeric_key_story(),
        shifting_story(),
        condition_story(),
        atomic_story(),
        diff_story(),
    ]


def render_stories() -> str:
    blocks = []
    for story in stories():
        blocks.append(story.title)
        blocks.extend(f"  {line}" for line in story.lines)
        blocks.append("  -> holds" if story.held else "  -> BROKEN")
        blocks.append("")
    return "\n".join(blocks) + "\n"
