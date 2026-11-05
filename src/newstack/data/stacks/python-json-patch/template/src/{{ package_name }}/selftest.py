"""Checks that run without pytest, so the CLI can prove itself anywhere."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from . import cli as cli_module
from . import demo
from .diff import diff, round_trips
from .patch import PatchError, TestFailed, apply, equal
from .pointer import PointerError, index_of, parse, render, resolve

CHECKS = 0
FAILED = 0
FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS, FAILED
    CHECKS += 1
    if condition:
        return
    FAILED += 1
    print(f"FAIL {name}" + (f": {detail}" if detail else ""))


def refuses(name: str, kind, action) -> None:
    try:
        action()
    except kind as error:
        check(name, True)
        check(f"{name} explains itself", len(str(error)) > 10, str(error))
    except Exception as error:
        check(name, False, f"raised {type(error).__name__}: {error}")
    else:
        check(name, False, "nothing was raised")


def quiet(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli_module.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue()


def run() -> None:
    check("the root pointer is the empty string", parse("") == ())
    check("a pointer splits into segments", parse("/a/b") == ("a", "b"))
    check("an escape is undone", parse("/a~1b") == ("a/b",))
    check("the tilde escape is undone", parse("/m~0n") == ("m~n",))
    check("a trailing slash is an empty key", parse("/a/") == ("a", ""))
    check("render escapes a slash", render(("a/b",)) == "/a~1b")
    check("render escapes a tilde", render(("m~n",)) == "/m~0n")
    check("render of the root is empty", render(()) == "")
    check("a pointer round trips", parse(render(("a/b", "m~n"))) == ("a/b", "m~n"))
    refuses("a pointer without a slash is refused", PointerError, lambda: parse("a/b"))
    refuses("an undefined escape is refused", PointerError, lambda: parse("/a~2b"))
    refuses("a non-string pointer is refused", PointerError, lambda: parse(3))

    check("a key is read from an object", resolve({"0": "x"}, "/0") == "x")
    check("an index is read from a list", resolve(["a", "b"], "/1") == "b")
    check("nested values are reachable", resolve({"a": [{"b": 2}]}, "/a/0/b") == 2)
    refuses("a missing key is refused", PointerError, lambda: resolve({"a": 1}, "/b"))
    refuses("'-' is not a readable index", PointerError, lambda: resolve(["a"], "/-"))
    refuses("a leading zero is not an index", PointerError, lambda: index_of("01", 5))
    refuses("an index past the end is refused", PointerError, lambda: index_of("3", 2))
    refuses("a scalar has no children", PointerError, lambda: resolve({"a": 1}, "/a/b"))

    check("integers and floats compare by value", equal(1, 1.0))
    check("a boolean is not the number one", not equal(True, 1))
    check("a string is not a number", not equal("1", 1))
    check("objects compare key by key", equal({"a": 1, "b": 2}, {"b": 2, "a": 1}))
    check("lists compare in order", not equal([1, 2], [2, 1]))
    check("nested values compare", equal({"a": [1, {"b": 2}]}, {"a": [1, {"b": 2}]}))

    document = {"a": 1, "items": ["x", "z"], "meta": {"deep": [1, 2]}}
    added = apply(document, [{"op": "add", "path": "/b", "value": 2}])
    check("add sets a new key", added["b"] == 2)
    check("the original document is untouched", "b" not in document)
    inserted = apply(document, [{"op": "add", "path": "/items/1", "value": "y"}])
    check("add inserts into a list", inserted["items"] == ["x", "y", "z"])
    appended = apply(document, [{"op": "add", "path": "/items/-", "value": "end"}])
    check("'-' appends", appended["items"] == ["x", "z", "end"])
    refuses("an index past the end is refused on add", PatchError,
            lambda: apply(document, [{"op": "add", "path": "/items/9", "value": 1}]))
    check("remove deletes a key", apply(document, [{"op": "remove", "path": "/a"}]) == {
        "items": ["x", "z"], "meta": {"deep": [1, 2]}})
    refuses("removing a missing key is refused", PatchError,
            lambda: apply(document, [{"op": "remove", "path": "/nope"}]))
    refuses("removing the root is refused", PatchError,
            lambda: apply(document, [{"op": "remove", "path": ""}]))
    check("replace overwrites", apply(document, [
        {"op": "replace", "path": "/a", "value": 9}])["a"] == 9)
    refuses("replacing a missing target is refused", PatchError,
            lambda: apply(document, [{"op": "replace", "path": "/nope", "value": 1}]))
    check("replace can replace the whole document",
          apply(document, [{"op": "replace", "path": "", "value": {"only": True}}])
          == {"only": True})

    moved = apply(document, [{"op": "move", "from": "/a", "path": "/meta/a"}])
    check("move removes the source", "a" not in moved)
    check("move writes the target", moved["meta"]["a"] == 1)
    refuses("a move into its own child is refused", PatchError,
            lambda: apply(document, [{"op": "move", "from": "/meta", "path": "/meta/x"}]))
    check("a move onto itself changes nothing",
          apply(document, [{"op": "move", "from": "/a", "path": "/a"}]) == document)
    copied = apply(document, [{"op": "copy", "from": "/meta", "path": "/copy"}])
    copied["copy"]["deep"].append(3)
    check("copy is a deep copy", document["meta"]["deep"] == [1, 2])

    check("a test that holds changes nothing",
          apply(document, [{"op": "test", "path": "/a", "value": 1}]) == document)
    refuses("a test that fails is refused", TestFailed,
            lambda: apply(document, [{"op": "test", "path": "/a", "value": 2}]))
    patch = [{"op": "add", "path": "/b", "value": 1},
             {"op": "replace", "path": "/nope", "value": 1},
             {"op": "add", "path": "/c", "value": 1}]
    refuses("a patch with a bad operation is refused", PatchError, lambda: apply(document, patch))
    check("the refused patch applied nothing", equal(
        document, {"a": 1, "items": ["x", "z"], "meta": {"deep": [1, 2]}}))
    refuses("a single operation is not a patch", PatchError,
            lambda: apply(document, {"op": "add", "path": "/b", "value": 1}))
    refuses("an unknown operation is refused", PatchError,
            lambda: apply(document, [{"op": "frobnicate", "path": "/a"}]))
    refuses("an operation without a path is refused", PatchError,
            lambda: apply(document, [{"op": "add", "value": 1}]))
    refuses("an add without a value is refused", PatchError,
            lambda: apply(document, [{"op": "add", "path": "/z"}]))

    before = json.loads((FIXTURES / "document.json").read_text())
    after = json.loads((FIXTURES / "after.json").read_text())
    operations = diff(before, after)
    check("the diff round trips", round_trips(before, after))
    check("the diff is not empty", len(operations) > 0)
    check("an equal pair diffs to nothing", diff(before, before) == [])
    check("a number and its float are the same document", diff({"a": 1}, {"a": 1.0}) == [])
    check("a list shrink diffs to removals",
          [op["op"] for op in diff([1, 2, 3], [1])] == ["remove", "remove"])

    code, out = quiet(["apply", "--document", str(FIXTURES / "document.json"),
                       "--patch", str(FIXTURES / "changes.json")])
    check("the apply command exits zero", code == 0, out)
    check("the apply command counts its operations", "operations   7" in out, out)
    code, out = quiet(["check", "--document", str(FIXTURES / "document.json"),
                       "--patch", str(FIXTURES / "changes.json")])
    check("the check command exits zero", code == 0, out)
    check("check says the document is unchanged", "unchanged" in out, out)
    code, out = quiet(["resolve", "--document", str(FIXTURES / "document.json"),
                       "/meta/a~1b"])
    check("resolve reads an escaped key", code == 0 and '"slash"' in out, out)
    code, out = quiet(["diff", "--before", str(FIXTURES / "document.json"),
                       "--after", str(FIXTURES / "after.json")])
    check("the diff command exits zero", code == 0, out)
    check("the diff command claims it applies", "applies      True" in out, out)
    code, _ = quiet(["apply", "--document", "/nonexistent/doc.json",
                     "--patch", str(FIXTURES / "changes.json")])
    check("a missing document exits two", code == 2, str(code))
    code, out = quiet(["demo"])
    check("the demo exits zero", code == 0, str(code))
    for story in demo.stories():
        check(f"demo story holds: {story.title}", story.held)
    check("the demo shows every story", demo.render_stories().count("-> holds") == 6)


def main() -> int:
    run()
    if FAILED:
        print(f"selftest: {FAILED} check(s) failed out of {CHECKS}")
        return 1
    print(f"selftest: {CHECKS} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
