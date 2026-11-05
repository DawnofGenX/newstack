"""One question — does this user see this flag? — answered with a reason and an audit trail."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .bucket import bucket_of
from .model import Flag, FlagSet

REASONS = ("unknown", "off", "targeted", "inside", "outside")
"""Every answer names one of these, so "the flag is on but they are outside it" is never a guess."""


@dataclass(frozen=True, slots=True)
class Decision:
    flag: str
    user: str
    variant: str
    reason: str
    bucket: int
    cutoff: int
    rollout: int

    def __post_init__(self) -> None:
        if self.reason not in REASONS:
            raise ValueError(
                f"unknown reason {self.reason!r}; expected one of {', '.join(REASONS)}"
            )

    @property
    def on(self) -> bool:
        return self.variant == "on"

    def line(self) -> str:
        head = f"{self.variant:<3} {self.reason:<9} {self.flag:<24}"
        return f"{head} bucket {self.bucket:>4} < {self.cutoff:>4}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "flag": self.flag,
            "user": self.user,
            "variant": self.variant,
            "reason": self.reason,
            "bucket": self.bucket,
            "cutoff": self.cutoff,
            "rollout": self.rollout,
        }


def decide(flags: FlagSet, name: str, user: str) -> Decision:
    """Precedence: unknown beats nothing, off beats everything, targeting beats the rollout."""
    if name not in flags:
        return Decision(name, user, "off", "unknown", 0, 0, 0)
    flag: Flag = flags[name]
    bucket = bucket_of(flag.salt, user)
    if not flag.enabled:
        return Decision(flag.name, user, "off", "off", bucket, flag.cutoff, flag.rollout)
    if user in flag.targets:
        return Decision(flag.name, user, "on", "targeted", bucket, flag.cutoff, flag.rollout)
    reason = "inside" if bucket < flag.cutoff else "outside"
    return Decision(
        flag.name,
        user,
        "on" if reason == "inside" else "off",
        reason,
        bucket,
        flag.cutoff,
        flag.rollout,
    )


def explain(flags: FlagSet, name: str, user: str) -> list[str]:
    """The decision plus the three rules it could have been, in the order they are applied."""
    decision = decide(flags, name, user)
    lines = [f"flag     {name}", f"user     {user}"]
    if name not in flags:
        return [*lines, f"decision {decision.variant} ({decision.reason})", "known    no"]
    flag: Flag = flags[name]
    lines.append(f"salt     {flag.salt}")
    lines.append(f"bucket   {decision.bucket} of 10000 ({decision.bucket / 100:.2f}%)")
    lines.append(f"cutoff   {decision.cutoff} (rollout {flag.rollout}%)")
    lines.append(f"enabled  {str(flag.enabled).lower()}")
    lines.append(f"targets  {', '.join(sorted(flag.targets)) if flag.targets else '-'}")
    verdict = "on" if decision.on else "off"
    lines.append(f"decision {verdict} ({decision.reason})")
    return lines
