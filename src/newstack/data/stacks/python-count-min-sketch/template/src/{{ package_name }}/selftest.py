"""Check the guarantees without pytest, so `selftest` works in a bare checkout."""

from __future__ import annotations

import io
import math
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from . import cli as command_line
from .measure import filled, report, skewed_counts, top
from .sketch import CountMinSketch, SketchError, epsilon, parse_sketch, row_hashes

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))


def refuses(name: str, kind: type[BaseException], call, needle: str = "") -> None:
    try:
        call()
    except kind as error:
        check(name, needle in str(error), f"message: {error}")
    except BaseException as error:
        check(name, False, f"raised {type(error).__name__}, expected {kind.__name__}")
    else:
        check(name, False, "nothing was raised")


def quiet(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = command_line.main(argv)
    except SystemExit as stop:
        code = stop.code if isinstance(stop.code, int) else 2
    return code, out.getvalue(), err.getvalue()


def run() -> int:
    CHECKS.clear()

    # -- hashing --------------------------------------------------------------------
    first = row_hashes("alpha", 4)
    check("a hash is stable", first == row_hashes("alpha", 4))
    check("rows differ from each other", len(set(first)) == 4)
    check("different items hash differently", row_hashes("alpha", 1) != row_hashes("beta", 1))
    refuses("depth 0 is refused", SketchError, lambda: row_hashes("x", 0))
    refuses("depth above 8 is refused", SketchError, lambda: row_hashes("x", 9), "at most 8")

    # -- counters -------------------------------------------------------------------
    sketch = CountMinSketch(64, 4)
    sketch.add("a", 3)
    check("an estimate counts its own updates", sketch.estimate("a") == 3)
    check("an unseen item estimates 0", sketch.estimate("nothing") == 0)
    check("totals add up", (sketch.total, sketch.updates) == (3, 1))
    refuses("a zero count is refused", SketchError, lambda: sketch.add("a", 0))
    refuses("a negative count is refused", SketchError, lambda: sketch.add("a", -1))
    refuses("a bool count is refused", SketchError, lambda: sketch.add("a", True))
    refuses("width 0 is refused", SketchError, lambda: CountMinSketch(0, 4))
    refuses("depth 9 is refused", SketchError, lambda: CountMinSketch(64, 9))

    # -- the one-sided error --------------------------------------------------------
    counts = skewed_counts(120, 6_000)
    plain = filled(counts, 256, 4)
    found = report(plain, counts)
    check("no estimate is below the truth", found.underestimates == 0)
    check("the largest overestimate stays inside the promise", found.max_over <= found.bound)
    check(
        "the promise is e/width of the updates",
        math.isclose(plain.bound(), epsilon(256) * plain.total),
    )
    wider = report(filled(counts, 512, 4), counts)
    check("a wider sketch computes at least as well", wider.max_over <= found.max_over + 1)
    check("the mean overestimate is not negative", found.mean_over >= 0)

    # -- conservative update --------------------------------------------------------
    careful = report(filled(counts, 128, 4, conservative=True), counts)
    hasty = report(filled(counts, 128, 4), counts)
    check(
        "conservative update is never worse on the heavy items", careful.max_over <= hasty.max_over
    )

    # -- merging --------------------------------------------------------------------
    items = list(counts)
    first_half = {item: counts[item] for item in items[: len(items) // 2]}
    second_half = {item: counts[item] for item in items[len(items) // 2 :]}
    merged = filled(first_half, 128, 3).merge(filled(second_half, 128, 3))
    one_pass = filled(counts, 128, 3)
    check("merged rows equal a single pass", merged.rows == one_pass.rows)
    check("merged totals add", merged.total == one_pass.total)
    refuses(
        "a mismatched width cannot merge",
        SketchError,
        lambda: filled(counts, 64, 3).merge(filled(counts, 128, 3)),
        "would not line up",
    )
    refuses(
        "a conservative sketch cannot merge with a plain one",
        SketchError,
        lambda: filled(counts, 64, 3).merge(filled(counts, 64, 3, conservative=True)),
        "would not describe either half",
    )

    # -- the heavy items ------------------------------------------------------------
    heaviest = top(filled(counts, 1024, 4), counts, 5)
    true_top = [item for item, _ in sorted(counts.items(), key=lambda pair: -pair[1])[:5]]
    check("the heaviest items are recognised", [item for item, _, _ in heaviest] == true_top)
    check(
        "their estimates are close",
        all(abs(estimate - true) <= 3 for _, estimate, true in heaviest),
    )

    # -- persistence ----------------------------------------------------------------
    payload = sketch.as_dict()
    again = parse_sketch(payload)
    check("a sketch round-trips through JSON", again.as_dict() == payload)
    refuses("another type is refused", SketchError, lambda: parse_sketch({"type": "bloom"}))
    broken = {**payload, "rows": payload["rows"][:1]}
    refuses(
        "a missing row is refused",
        SketchError,
        lambda: parse_sketch(broken),
        "needs that many rows",
    )
    short = {**payload, "rows": [[0] * 8 for _ in payload["rows"]]}
    refuses("a short row is refused", SketchError, lambda: parse_sketch(short))
    negative = {**payload, "rows": [[-1] + [0] * 63 for _ in payload["rows"]]}
    refuses("a negative counter is refused", SketchError, lambda: parse_sketch(negative))

    # -- the command line -----------------------------------------------------------
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sketch.json"
        code, _, _ = quiet(["add", "--sketch", str(path), "--items", "a", "b", "a", "--count", "2"])
        check("add creates the sketch", code == command_line.EXIT_OK and path.exists())
        code, out, _ = quiet(["estimate", "--sketch", str(path), "--item", "a", "--json"])
        check("estimate reads 4 for two doubled adds", '"estimate": 4' in out)
        code, out, _ = quiet(["info", "--sketch", str(path)])
        check("info prints the promise", "promise" in out)
        left = Path(directory) / "left.json"
        right = Path(directory) / "right.json"
        quiet(["add", "--sketch", str(left), "--items", "a", "--count", "3", "--width", "64"])
        quiet(["add", "--sketch", str(right), "--items", "a", "--count", "2", "--width", "64"])
        out_path = Path(directory) / "merged.json"
        code, _, _ = quiet(
            ["merge", "--left", str(left), "--right", str(right), "--out", str(out_path)]
        )
        check("merge writes the union", code == command_line.EXIT_OK and out_path.exists())
        code, out, _ = quiet(["estimate", "--sketch", str(out_path), "--item", "a", "--json"])
        check("the merged estimate adds", '"estimate": 5' in out)
        code, _, err = quiet(
            ["estimate", "--sketch", str(Path(directory) / "nope.json"), "--item", "a"]
        )
        check("a missing sketch exits 2", code == command_line.EXIT_UNUSABLE, err)
        code, _, _ = quiet(["add", "--sketch", str(path), "--items", "a", "--count", "0"])
        check("a zero count on the command line exits 2", code == command_line.EXIT_UNUSABLE)
        code, _, _ = quiet(
            ["merge", "--left", str(path), "--right", str(left), "--out", str(out_path)]
        )
        check("merging different shapes exits 2", code == command_line.EXIT_UNUSABLE)
        code, out, _ = quiet(["demo"])
        check("demo exits 0", code == command_line.EXIT_OK)
        check("demo prints six stories", "6. " in out and out.count("\n") > 20)
        code, _, _ = quiet([])
        check("no command exits 2", code == 2)

    passed = sum(1 for _, held, _ in CHECKS if held)
    for name, held, detail in CHECKS:
        if not held:
            print(f"FAIL {name}: {detail}")
    print(f"selftest: {passed} of {len(CHECKS)} checks passed")
    return 0 if passed == len(CHECKS) else 1
