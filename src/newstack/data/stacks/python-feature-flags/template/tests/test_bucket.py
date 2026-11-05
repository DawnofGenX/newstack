"""Bucketing: stable across processes, salts independent, boundaries exact."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys

import pytest

from {{ package_name }} import bucket as subject

PACKAGE = "{{ package_name }}"


def test_a_bucket_is_stable() -> None:
    assert subject.bucket_of("checkout", "alice") == subject.bucket_of("checkout", "alice")


def test_a_bucket_is_inside_the_space() -> None:
    for user in ("alice", "bob", "user-000042"):
        assert 0 <= subject.bucket_of("s", user) < 10_000


def test_a_bucket_matches_the_documented_formula() -> None:
    expected = int(hashlib.sha256(b"checkout:alice").hexdigest()[:8], 16) % 10_000
    assert subject.bucket_of("checkout", "alice") == expected


def test_two_salts_are_independent_rollouts() -> None:
    same = sum(
        1
        for index in range(2000)
        if subject.bucket_of("checkout", f"u{index}") < 1000
        and subject.bucket_of("search", f"u{index}") < 1000
    )
    # Two independent 10% rollouts overlap on about 1% of a population; one shared salt would
    # overlap on 10% and put exactly the same people in both experiments.
    assert same < 60


def test_zero_percent_admits_nobody_and_hundred_admits_everybody() -> None:
    assert not subject.inside("s", "alice", 0)
    assert subject.inside("s", "alice", 100)


def test_the_boundary_is_the_cutoff_and_not_off_by_one() -> None:
    for percent in (1, 10, 50, 99):
        cutoff = percent * 100
        for index in range(200):
            user = f"u{index}"
            bucket = subject.bucket_of("s", user)
            assert subject.inside("s", user, percent) is (bucket < cutoff)


@pytest.mark.parametrize(("salt", "user"), [("", "alice"), ("s", ""), ("", "")])
def test_an_empty_salt_or_user_is_refused(salt: str, user: str) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        subject.bucket_of(salt, user)


def test_a_rollout_outside_zero_to_a_hundred_is_refused() -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        subject.inside("s", "alice", 101)


def test_the_bucket_does_not_depend_on_pythonhashseed() -> None:
    """The whole reason this file exists: `hash()` would move every user on every restart."""
    script = (
        "import importlib, sys; "
        "module = importlib.import_module(sys.argv[1] + '.bucket'); "
        "print(module.bucket_of('s', 'u'))"
    )
    seen = set()
    for seed in ("0", "1", "12345"):
        environment = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, "-c", script, PACKAGE],
            capture_output=True,
            text=True,
            env=environment,
            check=True,
        )
        seen.add(result.stdout.strip())
    assert len(seen) == 1, seen


def test_hash_would_have_moved_them() -> None:
    """The negative control: the same subprocess trick, with the thing we did not use."""
    seen = set()
    for seed in ("0", "1"):
        environment = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, "-c", "print(hash('u') % 10000)"],
            capture_output=True,
            text=True,
            env=environment,
            check=True,
        )
        seen.add(result.stdout.strip())
    assert len(seen) == 2, "hash() is supposed to be unstable here — has CPython changed?"


def test_spread_counts_every_user_once() -> None:
    counts = subject.spread("s", [f"u{index}" for index in range(1000)])
    assert len(counts) == 100
    assert sum(counts.values()) == 1000
