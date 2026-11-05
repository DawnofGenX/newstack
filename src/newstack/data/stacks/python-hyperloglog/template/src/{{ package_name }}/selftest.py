"""Checks that run without pytest, and that the CLI can run anywhere."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
from pathlib import Path

from . import cli as cli_module
from . import demo
from .cli import EXIT_BREACH, EXIT_OK, EXIT_UNUSABLE
from .hashing import hash64, hash64_biased
from .hll import MASK64, HyperLogLog, SketchError, parse_sketch, relative_error
from .measure import compare, least_precision_for

CHECKS = 0
FAILED = 0


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
    """Run the CLI with its output captured; SystemExit becomes its code."""
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli_module.main(argv)
    except SystemExit as exit_code:
        code = int(exit_code.code or 0)
    return code, out.getvalue()


def run() -> None:
    check("hash64 is deterministic", hash64("alpha") == hash64("alpha"))
    check("hash64 separates neighbours", hash64("alpha") != hash64("beta"))
    check("hash64 stays inside 64 bits", 0 <= hash64("alpha") <= MASK64, str(hash64("alpha")))
    check("the biased hash differs", hash64_biased("7") != hash64("7"))
    check("the biased hash has no low entropy", hash64_biased("7") & 0xFFFFFFFF == 0)

    refusals = [
        ("a precision below four is refused", 3),
        ("a precision above eighteen is refused", 19),
        ("a boolean precision is refused", True),
    ]
    for name, precision in refusals:
        refuses(name, SketchError, lambda precision=precision: HyperLogLog(precision))
    refuses("a non-integer precision is refused", SketchError, lambda: HyperLogLog("14"))
    refuses("a short register array is refused", SketchError,
            lambda: HyperLogLog(4, bytearray(15)))
    refuses("an unknown index mode is refused", SketchError,
            lambda: HyperLogLog(4, index_mode="middle"))

    sketch = HyperLogLog(4)
    check("an empty sketch has every register zero", sketch.zeros() == 16)
    check("an empty estimate is zero", sketch.count() == 0)
    sketch.add("alpha")
    check("one add raises one register", sketch.raised == 1)
    before = sketch.count()
    sketch.add("alpha")
    check("the same item twice raises nothing", sketch.raised == 1)
    check("the same item twice does not move the estimate", sketch.count() == before)
    check("adds are counted separately", sketch.added == 2)

    full = HyperLogLog(4)
    full.add_hash(0)
    check("an all-zero hash lands in register zero", full.registers[0] == full.rank_cap)
    check("the rank is capped", full.registers[0] == 64 - 4 + 1, str(full.registers[0]))
    top = HyperLogLog(4)
    top.add_hash(0xF << 60)
    check("the index comes from the top bits", top.registers[15] > 0, str(top.registers[15]))
    check("the top bits do not touch register zero", top.registers[0] == 0)

    small = HyperLogLog(12)
    small.add("only-one")
    check("one distinct item estimates as one", small.count() == 1, str(small.count()))

    large = HyperLogLog(14)
    for number in range(10_000):
        large.add(f"user:{number}")
    comparison = compare(large, 10_000)
    check("10,000 items stay inside the promise", comparison.within, comparison.line())
    check("the promise is one point zero four over root m",
          abs(relative_error(14) - 1.04 / 128) < 1e-12)

    left = HyperLogLog(10)
    right = HyperLogLog(10)
    for number in range(600):
        (left if number % 2 else right).add(f"item:{number}")
    direct = HyperLogLog(10)
    for number in range(600):
        direct.add(f"item:{number}")
    before = bytes(left.registers)
    merged = left.merged(right)
    check("merging equals one pass", merged.registers == direct.registers)
    check("merging keeps the estimate", merged.count() == direct.count())
    check("merging adds the add counts", merged.added == left.added + right.added)
    check("a merge does not mutate the left sketch", bytes(left.registers) == before)
    check("the merged sketch is a separate object", merged is not left)
    refuses("merging another precision is refused", SketchError,
            lambda: HyperLogLog(10).merged(HyperLogLog(12)))
    refuses("merging a low-index sketch is refused", SketchError,
            lambda: HyperLogLog(10).merged(HyperLogLog(10, index_mode="low")))
    refuses("merging a non-sketch is refused", SketchError, lambda: HyperLogLog(10).merged(7))

    payload = large.as_dict()
    restored = parse_sketch(payload)
    check("a sketch round-trips through JSON", restored.registers == large.registers)
    check("a round-trip keeps the add count", restored.added == large.added)
    check("a round-trip keeps the estimate", restored.count() == large.count())
    refuses("a foreign type is refused", SketchError, lambda: parse_sketch({"type": "set"}))
    refuses("a sketch without precision is refused", SketchError,
            lambda: parse_sketch({"type": "hyperloglog", "registers": "00"}))
    refuses("non-hexadecimal registers are refused", SketchError,
            lambda: parse_sketch({"type": "hyperloglog", "precision": 4, "registers": "zz"}))
    refuses("registers of the wrong length are refused", SketchError,
            lambda: parse_sketch({"type": "hyperloglog", "precision": 4, "registers": "00"}))
    refuses("a missing register string is refused", SketchError,
            lambda: parse_sketch({"type": "hyperloglog", "precision": 4}))
    refuses("a negative add count is refused", SketchError,
            lambda: parse_sketch({"type": "hyperloglog", "precision": 4,
                                  "registers": (bytearray(16).hex()), "added": -1}))
    check("least_precision_for finds the first that promises the error",
          least_precision_for(0.02) == 12)

    for story in demo.stories():
        check(f"demo story holds: {story.title}", story.held)
    rendered = demo.render()
    check("the demo prints every story", rendered.count("-> holds") == len(demo.stories()))
    check("the demo does not claim anything broken", "BROKEN" not in rendered)

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        items = base / "items.txt"
        items.write_text("\n".join(f"item:{number}" for number in range(500)) + "\n",
                         encoding="utf-8")
        sketch_path = base / "sketch.json"
        code, out = quiet(["build", "--input", str(items), "--sketch", str(sketch_path),
                           "--precision", "10"])
        check("build succeeds", code == EXIT_OK, str(code))
        check("build reports the item count", "items     500" in out, out)
        check("build writes the sketch", sketch_path.exists())
        code, out = quiet(["estimate", "--sketch", str(sketch_path), "--expect", "500"])
        check("an estimate inside the promise exits zero", code == EXIT_OK, out)
        code, out = quiet(["estimate", "--sketch", str(sketch_path), "--expect", "5000"])
        check("an estimate outside the promise exits one", code == EXIT_BREACH, str(code))
        code, out = quiet(["info", "--sketch", str(sketch_path), "--json"])
        check("info prints JSON", json.loads(out)["registers"] == 1024, out)
        other = base / "other.json"
        code, _ = quiet(["build", "--input", str(items), "--sketch", str(other),
                         "--precision", "12"])
        code, out = quiet(["merge", "--left", str(sketch_path), "--right", str(other),
                           "--out", str(base / "merged.json")])
        check("merging different precisions exits two", code == EXIT_UNUSABLE, str(code))
        code, out = quiet(["estimate", "--sketch", str(base / "missing.json")])
        check("a missing sketch exits two", code == EXIT_UNUSABLE, str(code))
        broken = base / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        code, out = quiet(["estimate", "--sketch", str(broken)])
        check("a corrupt sketch exits two", code == EXIT_UNUSABLE, str(code))
    code, out = quiet(["demo"])
    check("the demo command exits zero", code == EXIT_OK, str(code))
    check("the demo command prints the stories", "precision buys accuracy" in out, out)


def main() -> int:
    run()
    if FAILED:
        print(f"selftest: {FAILED} check(s) failed out of {CHECKS}")
        return 1
    print(f"selftest: {CHECKS} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
