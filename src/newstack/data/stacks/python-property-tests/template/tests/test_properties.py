"""The invariants, checked on generated inputs rather than on examples.

Two settings carry the weight here and both are deliberate:

``derandomize=True``  - CI draws the same inputs every run, so a green build stays
                        green and a red one reproduces from the printed counterexample.
``database=None``     - hypothesis otherwise replays what it learned into
                        `.hypothesis/`, which turns "passed locally" into "failed on
                        the runner" for reasons nobody can see in the diff.
``deadline=None``     - the default 200 ms deadline measures the machine, not the code,
                        and a loaded CI box trips it on a test that is perfectly fast.
"""

from __future__ import annotations

import itertools

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from {{ package_name }}.intervals import (
    Interval,
    coverage,
    expand,
    intersect,
    normalize,
    points_to_intervals,
    subtract,
)

SETTINGS = settings(
    derandomize=True,
    database=None,
    deadline=None,
    max_examples=60,
    suppress_health_check=[HealthCheck.too_slow],
)

POINTS = st.integers(min_value=-12, max_value=12)
RUNS = st.lists(
    st.tuples(POINTS, POINTS).map(lambda pair: (min(pair), max(pair))),
    max_size=6,
)


@SETTINGS
@given(items=RUNS)
def test_normalised_output_is_sorted_disjoint_and_non_empty(items) -> None:
    result = normalize(items)
    assert all(not piece.empty for piece in result), "an empty interval survived"
    assert [piece.start for piece in result] == sorted(piece.start for piece in result)
    for earlier, later in itertools.pairwise(result):
        assert earlier.end < later.start, f"{earlier} and {later} overlap or touch"


@SETTINGS
@given(items=RUNS)
def test_normalize_is_idempotent(items) -> None:
    once = normalize(items)
    assert normalize(once) == once


@SETTINGS
@given(items=RUNS)
def test_coverage_matches_the_set_of_points(items) -> None:
    points = set(expand(items))
    assert coverage(items) == len(points)
    assert coverage(items) == sum(piece.length for piece in points_to_intervals(points))


@SETTINGS
@given(left=RUNS, right=RUNS)
def test_intersection_plus_subtraction_reconstructs_the_left_side(left, right) -> None:
    assert coverage(intersect(left, right)) + coverage(subtract(left, right)) == coverage(left)


@SETTINGS
@given(left=RUNS, right=RUNS)
def test_union_plus_intersection_counts_each_point_twice(left, right) -> None:
    both = coverage(left) + coverage(right)
    assert both == coverage(list(left) + list(right)) + coverage(intersect(left, right))


@SETTINGS
@given(left=RUNS, right=RUNS)
def test_intersection_is_contained_in_both_sides(left, right) -> None:
    shared = set(expand(intersect(left, right)))
    assert shared <= set(expand(left))
    assert shared <= set(expand(right))


@SETTINGS
@given(left=RUNS, right=RUNS)
def test_subtraction_never_grows_a_set(left, right) -> None:
    assert set(expand(subtract(left, right))) <= set(expand(left))


def test_shrinking_finds_a_minimal_counterexample() -> None:
    """`find` reports the smallest input that fails, which is the whole point.

    The property is not "the naive sum is right" - it is wrong on purpose. It is
    "the two implementations agree", and the search hands back the shortest input
    that breaks it instead of whatever random draw happened to fail first.
    """
    from hypothesis import find

    from {{ package_name }}.cli import naive_coverage

    def disagrees(items) -> bool:
        return naive_coverage([Interval(start, end) for start, end in items]) != coverage(items)

    smallest = find(RUNS, disagrees, settings=settings(derandomize=True, database=None,
                                                      deadline=None, max_examples=200))
    assert len(smallest) == 2, f"expected the minimal pair, got {smallest}"
    assert len({tuple(pair) for pair in smallest}) == 1, (
        "an overlap of two distinct runs also works"
    )


class CoverageMachine(RuleBasedStateMachine):
    """The clever code against a set of integers - an oracle nobody had to write twice.

    Every rule mutates both the interval bookkeeping and the set; the invariant
    then compares them. Bugs that live in the *sequence* of operations (a subtract
    that shifts a boundary left, a merge that swallows a gap) show up here and
    nowhere in a single-call test.
    """

    def __init__(self) -> None:
        super().__init__()
        self.intervals: list[Interval] = []
        self.model: set[int] = set()

    @initialize()
    def start_empty(self) -> None:
        self.intervals = []
        self.model = set()

    @rule(start=st.integers(-6, 6), length=st.integers(0, 5))
    def add(self, start: int, length: int) -> None:
        end = start + length
        self.intervals.append(Interval(start, end))
        self.model.update(range(start, end))

    @rule(start=st.integers(-6, 6), length=st.integers(0, 5))
    def remove(self, start: int, length: int) -> None:
        end = start + length
        self.intervals = subtract(self.intervals, [(start, end)])
        self.model.difference_update(range(start, end))

    @invariant()
    def coverage_matches_the_model(self) -> None:
        assert coverage(self.intervals) == len(self.model)
        assert set(expand(self.intervals)) == self.model


TestCoverageMachine = CoverageMachine.TestCase
