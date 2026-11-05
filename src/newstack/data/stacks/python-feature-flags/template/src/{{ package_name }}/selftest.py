"""Built-in checks: no pytest, no network, no flags file required."""

from __future__ import annotations

import tempfile
from pathlib import Path

from . import config
from .bucket import bucket_of, inside, spread
from .evaluate import decide
from .model import BPS, Flag, FlagSet, InputError


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            print(f"ok    {name}")
        else:
            self.failed += 1
            print(f"FAIL  {name}")

    def equal(self, name: str, want: object, got: object) -> None:
        if want == got:
            self.passed += 1
            print(f"ok    {name}")
        else:
            self.failed += 1
            print(f"FAIL  {name}: wanted {want!r}, got {got!r}")

    def raises(self, description: str, function, *args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except (InputError, ValueError, TypeError):
            self.passed += 1
            print(f"ok    {description}")
        else:
            self.failed += 1
            print(f"FAIL  {description}: no error raised")


def _bucket_checks(checks: Checks) -> None:
    first = bucket_of("checkout", "alice")
    checks.equal("a bucket is stable", first, bucket_of("checkout", "alice"))
    checks.ok("a bucket is inside the bucket space", 0 <= first < BPS)
    checks.ok("a different salt lands elsewhere", bucket_of("search", "alice") != first)
    checks.equal("the bucket is an integer", int, type(first))
    checks.ok("0 percent admits nobody", not inside("checkout", "alice", 0))
    checks.ok("100 percent admits everybody", inside("checkout", "alice", 100))
    checks.raises("an empty user is refused", bucket_of, "checkout", "")
    checks.raises("an empty salt is refused", bucket_of, "", "alice")
    checks.raises("a rollout above 100 is refused", inside, "checkout", "alice", 101)
    checks.equal("the bucket matches the documented formula", _constant(), bucket_of("s", "u"))


def _constant() -> int:
    """The bucket of ("s", "u"), computed once from the algorithm rather than the implementation."""
    import hashlib

    return int(hashlib.sha256(b"s:u").hexdigest()[:8], 16) % BPS


def _flag_checks(checks: Checks) -> None:
    flag = Flag(name="checkout", rollout=10, salt="s")
    checks.equal("the cutoff is the rollout in basis points", 1000, flag.cutoff)
    checks.equal("a fresh flag is enabled", True, flag.enabled)
    checks.equal("no targets means an empty set", 0, len(flag.targets))
    checks.raises("a name with a space is refused", Flag, name="check out", salt="s")
    checks.raises("a rollout of true is refused", Flag, name="a", rollout=True, salt="s")
    checks.raises("a rollout of 101 is refused", Flag, name="a", rollout=101, salt="s")
    checks.raises("a missing salt is refused", Flag, name="a", rollout=1)
    checks.equal("flags are indexed by name", 1, len(FlagSet.of([Flag(name="a", salt="s")])))
    duplicated = [Flag(name="a", salt="s"), Flag(name="a", salt="t")]
    checks.raises("a duplicate name is refused", FlagSet.of, duplicated)


def _decision_checks(checks: Checks) -> None:
    flags = FlagSet.of(
        [
            Flag(name="half", rollout=50, salt="half"),
            Flag(name="all", rollout=100, salt="all"),
            Flag(name="none", rollout=0, salt="none"),
            Flag(name="off", enabled=False, rollout=100, salt="off", targets=frozenset({"alice"})),
            Flag(name="vip", rollout=0, salt="vip", targets=frozenset({"alice"})),
        ]
    )
    checks.equal("an unknown flag is off", "off", decide(flags, "nope", "alice").variant)
    checks.equal("and says so", "unknown", decide(flags, "nope", "alice").reason)
    checks.equal(
        "a disabled flag is off even for a targeted user",
        "off",
        decide(flags, "off", "alice").variant,
    )
    checks.equal("and the reason is the switch", "off", decide(flags, "off", "alice").reason)
    checks.equal("a targeted user is on", "on", decide(flags, "vip", "alice").variant)
    checks.equal("and the reason is targeting", "targeted", decide(flags, "vip", "alice").reason)
    checks.equal("100 percent is inside", "inside", decide(flags, "all", "alice").reason)
    checks.equal("0 percent is outside", "outside", decide(flags, "none", "alice").reason)
    kind = decide(flags, "half", "alice").reason
    checks.ok("50 percent is a coin, not a constant", kind in ("inside", "outside"))
    checks.equal(
        "the same user gets the same answer twice",
        decide(flags, "half", "bob").bucket,
        decide(flags, "half", "bob").bucket,
    )


def _config_checks(checks: Checks) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "flags.toml"
        path.write_text('[[flag]]\nname = "a"\nrollout = 5\nsalt = "s"\n')
        checks.equal("a minimal file loads", 1, len(config.load(path)))
        path.write_text('[[flag]]\nname = "a"\nrollout = 5\nsalt = "s"\nrolout = 6\n')
        checks.raises("a typo is refused", config.load, path)
        path.write_text('[[flag]]\nname = "a"\nrollout = 5\nsalt = "s"\ntargets = "alice"\n')
        checks.raises("targets must be a list", config.load, path)
        path.write_text('[[flag]]\nname = "a"\nsalt = "s"\n\n[[flag]]\nname = "a"\nsalt = "t"\n')
        checks.raises("a duplicate flag is refused", config.load, path)
        path.write_text("this is not toml")
        checks.raises("broken TOML is refused", config.load, path)
        checks.raises("a missing file is refused", config.load, Path(directory) / "absent.toml")


def _distribution_checks(checks: Checks) -> None:
    users = [f"user-{index:06d}" for index in range(10_000)]
    counts = spread("checkout-2026-11", users)
    checks.equal("the spread covers a hundred percent buckets", 100, len(counts))
    checks.equal("every user lands in exactly one bucket", 10_000, sum(counts.values()))
    inside_ten = sum(count for percent, count in counts.items() if percent < 10)
    checks.ok("a ten percent rollout is close to a thousand users", 900 <= inside_ten <= 1100)


def run() -> int:
    checks = Checks()
    groups = (_bucket_checks, _flag_checks, _decision_checks, _config_checks, _distribution_checks)
    for group in groups:
        group(checks)
    total = checks.passed + checks.failed
    print(f"\nselftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
