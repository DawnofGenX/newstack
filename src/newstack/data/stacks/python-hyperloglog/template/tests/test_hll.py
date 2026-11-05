from __future__ import annotations

import json

import pytest

from {{ package_name }} import hll as subject


def filled(precision: int, count: int, prefix: str = "user"):
    sketch = subject.HyperLogLog(precision)
    for number in range(count):
        sketch.add(f"{prefix}:{number}")
    return sketch


def test_precision_is_bounded() -> None:
    for precision in (3, 19):
        with pytest.raises(subject.SketchError, match="outside"):
            subject.HyperLogLog(precision)
    with pytest.raises(subject.SketchError, match="whole number"):
        subject.HyperLogLog(True)


def test_a_short_register_array_is_refused() -> None:
    with pytest.raises(subject.SketchError, match="needs 16 register"):
        subject.HyperLogLog(4, bytearray(15))


def test_an_empty_sketch_estimates_zero() -> None:
    sketch = subject.HyperLogLog(10)
    assert sketch.zeros() == 1024
    assert sketch.count() == 0


def test_the_rank_is_capped_by_the_precision() -> None:
    sketch = subject.HyperLogLog(4)
    sketch.add_hash(0)
    assert sketch.rank_cap == 61
    assert sketch.registers[0] == 61


def test_repeating_an_item_does_not_raise_a_register_twice() -> None:
    sketch = subject.HyperLogLog(12)
    sketch.add("alpha")
    raised = sketch.raised
    sketch.add("alpha")
    assert sketch.raised == raised
    assert sketch.added == 2


def test_ten_thousand_items_stay_inside_the_promise() -> None:
    sketch = filled(14, 10_000)
    error = abs(sketch.count() - 10_000) / 10_000
    assert error <= 4 * subject.relative_error(14), error


def test_one_item_estimates_as_one() -> None:
    sketch = subject.HyperLogLog(12)
    sketch.add("only")
    assert sketch.count() == 1


def test_merging_equals_one_pass() -> None:
    left = filled(12, 500, prefix="even")
    right = filled(12, 500, prefix="odd")
    direct = subject.HyperLogLog(12)
    for number in range(500):
        direct.add(f"even:{number}")
        direct.add(f"odd:{number}")
    merged = left.merged(right)
    assert merged.registers == direct.registers
    assert merged.count() == direct.count()


def test_merging_different_precisions_is_refused() -> None:
    with pytest.raises(subject.SketchError, match="reinterpreted"):
        subject.HyperLogLog(12).merged(subject.HyperLogLog(14))


def test_merging_different_index_modes_is_refused() -> None:
    with pytest.raises(subject.SketchError, match="index"):
        subject.HyperLogLog(12).merged(subject.HyperLogLog(12, index_mode="low"))


def test_merging_something_else_is_refused() -> None:
    with pytest.raises(subject.SketchError, match="cannot merge"):
        subject.HyperLogLog(12).merged({"type": "hyperloglog"})


def test_a_serialised_sketch_round_trips() -> None:
    sketch = filled(10, 700)
    restored = subject.parse_sketch(json.loads(json.dumps(sketch.as_dict())))
    assert restored.registers == sketch.registers
    assert restored.added == sketch.added
    assert restored.count() == sketch.count()


def test_a_foreign_payload_is_refused() -> None:
    with pytest.raises(subject.SketchError, match="not a hyperloglog"):
        subject.parse_sketch({"type": "set"})
    with pytest.raises(subject.SketchError, match="whole-number precision"):
        subject.parse_sketch({"type": "hyperloglog", "registers": "00"})
    with pytest.raises(subject.SketchError, match="not hexadecimal"):
        subject.parse_sketch({"type": "hyperloglog", "precision": 4, "registers": "zz"})
    with pytest.raises(subject.SketchError, match="needs 16 register"):
        subject.parse_sketch({"type": "hyperloglog", "precision": 4, "registers": "00"})


def test_the_estimate_is_a_float_and_the_count_is_a_rounding_of_it() -> None:
    sketch = filled(10, 300)
    assert isinstance(sketch.estimate(), float)
    assert sketch.count() == round(sketch.estimate())


def test_small_cardinalities_use_linear_counting() -> None:
    sketch = filled(14, 3)
    # Below 2.5 * m the raw harmonic estimate is biased; linear counting is exact here.
    assert sketch.zeros() > 0
    assert sketch.count() == 3
