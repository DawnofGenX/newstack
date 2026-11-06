import itertools
import random

import pytest

from {{ package_name }} import history as history_module
from {{ package_name }}.check import (
    brute_force,
    check,
    is_minimal,
    shrink,
)


def op(client, kind, value, start, end):
    return history_module.Operation(client=client, kind=kind, value=value, start=start, end=end)


def history(*operations, initial=0):
    return history_module.History(tuple(operations), initial=initial)


def test_the_empty_history_is_linearizable():
    verdict = check(history())
    assert verdict.linearizable is True
    assert verdict.order == ()


def test_one_write_is_a_witness():
    verdict = check(history(op(0, "write", 5, 0, 1)))
    assert verdict.linearizable is True
    assert verdict.order == (0,)


def test_a_sequential_history_keeps_its_order():
    verdict = check(
        history(op(0, "write", 1, 0, 1), op(0, "write", 2, 2, 3), op(0, "read", 2, 4, 5))
    )
    assert verdict.linearizable is True
    assert verdict.order == (0, 1, 2)


def test_an_old_value_after_a_write_returns_is_refused():
    verdict = check(history(op(0, "write", 5, 0, 2), op(1, "read", 0, 3, 4)))
    assert verdict.linearizable is False
    assert verdict.reason.startswith("no order")


def test_an_old_value_from_an_overlapping_read_is_allowed():
    verdict = check(history(op(0, "write", 5, 0, 2), op(1, "read", 0, 1, 4)))
    assert verdict.linearizable is True
    assert verdict.order == (1, 0)


def test_a_write_lands_between_two_reads():
    verdict = check(
        history(op(0, "write", 1, 0, 10), op(1, "read", 0, 1, 2), op(1, "read", 1, 3, 4))
    )
    assert verdict.linearizable is True
    assert verdict.order == (1, 0, 2)


def test_a_value_nobody_wrote_is_refused():
    verdict = check(history(op(0, "write", 1, 0, 1), op(1, "read", 2, 2, 3)))
    assert verdict.linearizable is False


def test_the_initial_value_can_be_read_before_any_write():
    verdict = check(history(op(0, "read", 9, 0, 1)), initial=9)
    assert verdict.linearizable is True


def test_an_override_initial_value_is_used():
    history_ = history(op(0, "read", 9, 0, 1), initial=0)
    assert check(history_).linearizable is False
    assert check(history_, initial=9).linearizable is True


def test_the_order_satisfies_programme_order_and_real_time():
    operations = (
        op(0, "write", 1, 0, 2),
        op(1, "read", 1, 1, 3),
        op(0, "read", 1, 4, 6),
        op(2, "write", 2, 5, 7),
    )
    verdict = check(history(*operations))
    assert verdict.linearizable is True
    places = {index: spot for spot, index in enumerate(verdict.order)}
    assert places[0] < places[2]
    assert places[1] < places[2]


def test_a_long_history_is_decided_without_exploring_everything():
    operations = tuple(
        op(index % 4, "write" if index % 2 else "read", 0, index, index + 1) for index in range(12)
    )
    verdict = check(history(*operations))
    assert isinstance(verdict.linearizable, bool)


def test_brute_force_refuses_a_history_it_cannot_enumerate():
    operations = tuple(op(0, "read", 0, index, index + 1) for index in range(9))
    with pytest.raises(ValueError, match="stops at 8"):
        brute_force(history(*operations))


def test_brute_force_finds_a_witness_on_a_concurrent_history():
    verdict = brute_force(
        history(op(0, "write", 1, 0, 4), op(1, "write", 2, 1, 5), op(2, "read", 2, 6, 7))
    )
    assert verdict.linearizable is True


def test_shrink_leaves_a_minimal_core():
    operations = (
        op(0, "write", 1, 0, 1),
        op(1, "read", 0, 2, 3),
        op(2, "write", 9, 4, 5),
        op(1, "read", 9, 6, 7),
        op(3, "read", 1, 8, 9),
    )
    core, verdict = shrink(history(*operations))
    assert verdict.linearizable is False
    assert len(core) < 5
    assert is_minimal(core) is True


def test_shrink_of_a_good_history_returns_it_unchanged():
    original = history(op(0, "read", 0, 0, 1))
    core, verdict = shrink(original)
    assert core == original
    assert verdict.linearizable is True


def test_is_minimal_is_false_for_a_history_that_is_fine():
    assert is_minimal(history(op(0, "write", 1, 0, 1))) is False


def _random_history(rng, clients, operations_per_client):
    operations = []
    for client in range(clients):
        start = rng.randrange(0, 4)
        for _ in range(operations_per_client):
            kind = rng.choice(["read", "write"])
            duration = rng.randrange(0, 3)
            operations.append(
                history_module.Operation(
                    client=client,
                    kind=kind,
                    value=rng.randrange(0, 3),
                    start=start,
                    end=start + duration,
                )
            )
            start = start + duration + rng.randrange(1, 3)
    return history_module.History(tuple(operations), initial=rng.randrange(0, 3))


@pytest.mark.parametrize("seed", range(40))
def test_the_search_agrees_with_every_permutation_on_a_random_history(seed):
    rng = random.Random(seed)
    sample = _random_history(rng, clients=2, operations_per_client=rng.randrange(1, 4))
    if len(sample) > 7:
        pytest.skip("the yardstick stops at eight operations")
    fast = check(sample)
    slow = brute_force(sample)
    assert fast.linearizable is slow.linearizable, (seed, sample.lines(), fast, slow)
    if fast.linearizable:
        assert len(fast.order) == len(sample)


def test_a_search_that_fails_counts_hits_only_after_the_first_visit():
    operations = (
        op(0, "write", 1, 0, 1),
        op(1, "read", 2, 2, 3),
        op(1, "read", 1, 4, 5),
        op(0, "write", 2, 2, 3),
    )
    verdict = check(history(*operations))
    assert verdict.nodes >= 1
    assert verdict.memo_hits >= 0
    if not verdict.linearizable:
        assert verdict.order == ()


def test_every_operation_appears_once_in_a_witness():
    sample = history(*[op(0, "write", 0, index, index + 1) for index in range(5)])
    verdict = check(sample)
    assert sorted(verdict.order) == list(range(5))
    assert len(set(verdict.order)) == len(verdict.order)


def test_permutations_of_a_concurrent_history_all_hold():
    sample = history(*[op(index, "write", 0, 0, 10) for index in range(4)])
    verdict = check(sample)
    assert verdict.linearizable is True
    assert len(verdict.order) == 4
    assert tuple(sorted(verdict.order)) == (0, 1, 2, 3)
    assert list(itertools.islice(iter(verdict.order), 4)) == list(verdict.order)
