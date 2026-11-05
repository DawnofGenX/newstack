"""A flag, and what a flag is allowed to say."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

BPS = 10_000
"""The bucket space, in basis points: one percent is a hundred buckets."""

NAME = re.compile(r"^[a-z][a-z0-9-]*$")

VARIANTS = ("on", "off")


class InputError(ValueError):
    """The flags file, or the question asked of it, does not make sense."""


@dataclass(frozen=True, slots=True)
class Flag:
    name: str
    enabled: bool = True
    rollout: int = 0
    salt: str = ""
    targets: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not NAME.match(self.name):
            raise InputError(
                f"flag name {self.name!r} is not a slug (lowercase letters, digits and dashes)"
            )
        if isinstance(self.rollout, bool) or not isinstance(self.rollout, int):
            raise InputError(
                f"flag {self.name}: rollout must be an integer percent, got {self.rollout!r}"
            )
        if not 0 <= self.rollout <= 100:
            raise InputError(
                f"flag {self.name}: rollout must be between 0 and 100, got {self.rollout}"
            )
        if not self.salt:
            raise InputError(
                f"flag {self.name}: salt is required; without it the same users land in "
                "every flag's rollout"
            )
        if not isinstance(self.enabled, bool):
            raise InputError(f"flag {self.name}: enabled must be true or false")

    @property
    def cutoff(self) -> int:
        """The bucket a user must fall below to be inside the rollout."""
        return self.rollout * (BPS // 100)

    def line(self) -> str:
        state = "on " if self.enabled else "off"
        targets = f" targets={len(self.targets)}" if self.targets else ""
        return f"{self.name:<24} {state} {self.rollout:>3}%  salt={self.salt}{targets}"


@dataclass(frozen=True, slots=True)
class FlagSet:
    flags: dict[str, Flag]

    @classmethod
    def of(cls, flags: Iterable[Flag]) -> FlagSet:
        items = list(flags)
        table = {flag.name: flag for flag in items}
        if len(table) != len(items):
            seen: dict[str, int] = {}
            for flag in items:
                seen[flag.name] = seen.get(flag.name, 0) + 1
            duplicated = sorted(name for name, count in seen.items() if count > 1)
            raise InputError(f"duplicate flag(s): {', '.join(duplicated)}")
        return cls(table)

    def __getitem__(self, name: str) -> Flag:
        try:
            return self.flags[name]
        except KeyError:
            raise InputError(
                f"unknown flag {name!r}; known flags are: {', '.join(sorted(self.flags))}"
            ) from None

    def __contains__(self, name: object) -> bool:
        return name in self.flags

    def __iter__(self) -> Iterator[Flag]:
        return iter(self.flags.values())

    def __len__(self) -> int:
        return len(self.flags)
