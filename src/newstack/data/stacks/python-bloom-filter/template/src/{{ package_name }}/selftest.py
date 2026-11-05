"""Every claim the README makes, checked in one process."""

from __future__ import annotations

import contextlib
import io
import json
import math
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import bloom as core
from .bloom import Bloom, BloomFilterError, CountingBloom, parse_filter, sized_for
from .cli import main as cli_main
from .measure import false_negatives, false_positive_rate

PASSED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise SystemExit(f"selftest: FAILED {name}" + (f" ({detail})" if detail else ""))
    PASSED.append(name)


def equal(name: str, actual: object, expected: object) -> None:
    check(name, actual == expected, f"{actual!r} != {expected!r}")


def refuses(name: str, call: Callable[[], Any], needle: str = "") -> None:
    try:
        call()
    except BloomFilterError as error:
        check(name, needle in str(error), f"{error} does not contain {needle!r}")
        return
    raise SystemExit(f"selftest: FAILED {name} (it did not raise)")


def _quiet(call: Callable[[], Any]) -> tuple[Any, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        value = call()
    return value, buffer.getvalue()


def _filled(count: int, rate: float = 0.01, prefix: str = "present") -> Bloom:
    sizing = sized_for(count, rate)
    bloom = Bloom(sizing.m_bits, sizing.k_hashes)
    for number in range(count):
        bloom.add(f"{prefix}-{number}")
    return bloom


def _sharing_pair(bloom: Bloom) -> tuple[str, str]:
    seen: dict[int, str] = {}
    for number in range(1_000):
        item = f"candidate-{number}"
        for position in bloom.positions(item):
            other = seen.get(position)
            if other is not None:
                return other, item
            seen[position] = item
    raise SystemExit("selftest: FAILED could not find a sharing pair")


def _sizing_checks() -> None:
    sizing = sized_for(1_000, 0.01)
    equal("the textbook size is 9586 bits", sizing.m_bits, 9_586)
    equal("the optimum hash count is 7", sizing.k_hashes, 7)
    check("bits per item is near 9.59", abs(sizing.bits_per_item - 9.586) < 0.001)
    check(
        "the predicted rate is within 5% of the target",
        abs(sizing.predicted_rate - 0.01) < 0.0005,
        f"{sizing.predicted_rate:.6f}",
    )
    check("a tighter rate needs more bits", sized_for(1_000, 0.001).m_bits > sizing.m_bits)
    check("more items need more bits", sized_for(5_000, 0.01).m_bits > sizing.m_bits)
    optimum = sizing.m_bits / sizing.expected * math.log(2)
    check("the hash count is the rounded optimum", abs(sizing.k_hashes - optimum) <= 0.5)
    text = "\n".join(sizing.lines())
    check("the report names the bits", "bits        9586" in text)
    check("the report names the hashes", "hashes      7" in text)
    refuses("a zero item count is refused", lambda: sized_for(0, 0.01), "at least 1")
    refuses("a negative item count is refused", lambda: sized_for(-3, 0.01), "at least 1")
    refuses("a boolean item count is refused", lambda: sized_for(True, 0.01), "not an integer")
    refuses("a rate of zero is refused", lambda: sized_for(10, 0.0), "between 0 and 1")
    refuses("a rate of one is refused", lambda: sized_for(10, 1.0), "between 0 and 1")
    refuses("a negative rate is refused", lambda: sized_for(10, -0.5), "between 0 and 1")


def _guarantee_checks() -> None:
    bloom = _filled(2_000)
    items = [f"present-{number}" for number in range(2_000)]
    equal("nothing that was added is reported absent", false_negatives(bloom, items), [])
    check(
        "capacity leaves the filter about half full",
        0.45 < bloom.fill() < 0.6,
        f"{bloom.fill():.4f}",
    )
    estimate = bloom.estimate_items()
    check(
        "the estimate is near the real count",
        estimate is not None and 1_600 < estimate < 2_500,
        f"{estimate}",
    )
    measured = false_positive_rate(bloom, 20_000)
    predicted = bloom.predict_rate()
    check(
        "the measured rate tracks the predicted one",
        abs(measured - predicted) < 0.003,
        f"measured {measured:.4f} predicted {predicted:.4f}",
    )
    check("the measured rate is near the 1% target", 0.002 < measured < 0.02, f"{measured:.4f}")
    equal("a filter at its design capacity is not saturated", bloom.is_saturated(), False)


def _structure_checks() -> None:
    bloom = Bloom(1_024, 4)
    equal("an empty filter has no bits set", bloom.bits_set(), 0)
    equal("an empty filter answers no", bloom.might_contain("alpha"), False)
    equal("the first add sets every hash position", len(bloom.add("alpha")), 4)
    equal("re-adding sets nothing new", bloom.add("alpha"), ())
    equal("the bit count matches the hash count", bloom.bits_set(), 4)
    check(
        "every position is inside the array",
        all(0 <= position < 1_024 for position in bloom.positions("alpha")),
    )
    equal(
        "the same items always produce the same bits",
        _filled(100).as_dict(),
        _filled(100).as_dict(),
    )
    padded = Bloom(3, 1, b"\xff")
    equal("padding bits are not counted", padded.bits_set(), 3)
    equal("a padded filter is full", padded.fill(), 1.0)
    equal("a full filter has no estimate", padded.estimate_items(), None)
    equal("a full filter is saturated", padded.is_saturated(), True)


def _removal_checks() -> None:
    naive = Bloom(4_096, 3)
    counting = CountingBloom(4_096, 3)
    keeper, dropped = _sharing_pair(naive)
    for bloom in (naive, counting):
        bloom.add(keeper)
        bloom.add(dropped)
    naive.clear(dropped)
    counting.remove(dropped)
    equal("clearing a bit makes another item vanish", naive.might_contain(keeper), False)
    equal("a counter survives the same removal", counting.might_contain(keeper), True)
    equal("the removed item is gone", counting.might_contain(dropped), False)
    refuses(
        "removing an item that was never added is refused",
        lambda: counting.remove("ghost"),
        "no record of the add",
    )
    saturating = CountingBloom(8, 1)
    for _ in range(core.SATURATION + 5):
        saturating.add("same")
    equal("counters stop at 255", saturating.saturated_positions(), 1)
    encoded = str(saturating.as_dict()["counters"])
    check("saturation is visible in the encoding", encoded.startswith("ff"))


def _state_checks() -> None:
    original = _filled(300)
    rebuilt = parse_filter(json.loads(json.dumps(original.as_dict())))
    equal("a plain filter survives JSON", rebuilt.as_dict(), original.as_dict())
    equal("the rebuilt filter answers the same", rebuilt.might_contain("present-42"), True)
    counting = CountingBloom(512, 3)
    counting.add("alpha")
    round_trip = parse_filter(counting.as_dict())
    equal("a counting filter survives JSON", round_trip.as_dict(), counting.as_dict())
    check("the round trip keeps its type", isinstance(round_trip, CountingBloom))
    refuses("a non-object payload is refused", lambda: parse_filter([]), "JSON object")
    refuses(
        "an unknown type is refused",
        lambda: parse_filter({"type": "sieve"}),
        "unknown filter type",
    )
    refuses(
        "a missing bit count is refused",
        lambda: parse_filter({"type": "bloom", "k_hashes": 3, "bits": ""}),
        "has no m_bits",
    )
    refuses(
        "a short bit array is refused",
        lambda: parse_filter({"type": "bloom", "m_bits": 16, "k_hashes": 2, "bits": "00"}),
        "holds 1 byte",
    )
    refuses(
        "a non-hex bit array is refused",
        lambda: parse_filter({"type": "bloom", "m_bits": 8, "k_hashes": 2, "bits": "zz"}),
        "not hexadecimal",
    )
    refuses(
        "a short counter array is refused",
        lambda: parse_filter(
            {"type": "counting-bloom", "m_bits": 8, "k_hashes": 1, "counters": "0000"}
        ),
        "holds 2 counter",
    )
    refuses("a zero bit count is refused", lambda: Bloom(0, 1), "at least 1")
    refuses("a zero hash count is refused", lambda: Bloom(8, 0), "at least 1")


def _cli_checks() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "items.json"
        code, out = _quiet(
            lambda: cli_main(["create", "--filter", str(path), "--expected", "100"])
        )
        equal("create exits zero", code, 0)
        check("create names the file", "created" in out)
        code, _ = _quiet(lambda: cli_main(["check", "--filter", str(path), "--item", "alpha"]))
        equal("an empty filter says absent", code, 1)
        code, _ = _quiet(
            lambda: cli_main(["add", "--filter", str(path), "--item", "alpha"])
        )
        equal("add exits zero", code, 0)
        code, out = _quiet(
            lambda: cli_main(["check", "--filter", str(path), "--item", "alpha"])
        )
        equal("an added item is present", code, 0)
        check("the answer says maybe", "maybe: false positives are possible" in out)
        code, out = _quiet(
            lambda: cli_main(["check", "--filter", str(path), "--item", "alpha", "--json"])
        )
        check("json carries the answer", '"present": true' in out)
        code, out = _quiet(lambda: cli_main(["info", "--filter", str(path)]))
        equal("info exits zero on a healthy filter", code, 0)
        check("info reports healthy", "healthy" in out)
        code, _ = _quiet(
            lambda: cli_main(["create", "--filter", str(path), "--expected", "5"])
        )
        equal("a second create is refused", code, 2)
        code, _ = _quiet(
            lambda: cli_main(["check", "--filter", str(path) + ".gone", "--item", "x"])
        )
        equal("a missing filter is a usage error", code, 2)
        code, _ = _quiet(
            lambda: cli_main(["create", "--filter", str(path), "--expected", "0", "--force"])
        )
        equal("a zero expected count is a usage error", code, 2)
        code, out = _quiet(lambda: cli_main(["sized", "--expected", "1000", "--rate", "0.01"]))
        equal("sized exits zero", code, 0)
        check("sized prints the bits", "bits        9586" in out)
        code, out = _quiet(lambda: cli_main(["demo"]))
        equal("demo exits zero", code, 0)
        check("the demo shows removal failing", "removal is where the guarantee dies" in out)
        check("the demo shows saturation", "saturation is the failure mode" in out)


def main() -> int:
    PASSED.clear()
    _sizing_checks()
    _guarantee_checks()
    _structure_checks()
    _removal_checks()
    _state_checks()
    _cli_checks()
    print(f"selftest: {len(PASSED)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
