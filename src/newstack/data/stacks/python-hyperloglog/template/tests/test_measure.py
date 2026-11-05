from __future__ import annotations

from {{ package_name }} import hll as hll_subject
from {{ package_name }} import measure as subject


def test_a_perfect_estimate_has_no_error() -> None:
    sketch = hll_subject.HyperLogLog(14)
    for number in range(3):
        sketch.add(f"item:{number}")
    comparison = subject.compare(sketch, 3)
    assert comparison.error == 0.0
    assert comparison.within


def test_the_error_is_signed_so_direction_is_visible() -> None:
    sketch = hll_subject.HyperLogLog(14)
    for number in range(4000):
        sketch.add(f"item:{number}")
    comparison = subject.compare(sketch, 10_000)
    assert comparison.error < 0
    assert not comparison.within


def test_an_empty_sketch_reports_no_error_and_no_estimate() -> None:
    empty = subject.error_at(12, [], 0)
    assert empty.estimate == 0
    assert empty.error == 0.0


def test_least_precision_for_answers_with_the_first_that_fits() -> None:
    assert subject.least_precision_for(0.02) == 12
    assert subject.least_precision_for(0.009) == 14
    assert subject.least_precision_for(0.008) == 15
    assert subject.least_precision_for(0.5) == 4


def test_pre_hashing_gives_the_same_answer_as_adding() -> None:
    texts = [f"user:{number}" for number in range(2000)]
    sketch = hll_subject.HyperLogLog(12)
    for text in texts:
        sketch.add(text)
    pre_hashed = subject.error_at(12, [hll_subject.hash64(text) for text in texts], len(texts))
    assert pre_hashed.estimate == sketch.count()


def test_an_exact_set_costs_far_more_than_a_sketch() -> None:
    items = {f"user:{number}" for number in range(2000)}
    sketch = hll_subject.HyperLogLog(12)
    assert subject.set_memory(items) > sketch.bytes_used * 10
