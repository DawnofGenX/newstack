"""Why a version does or does not satisfy a range, one arm at a time."""

from __future__ import annotations

from dataclasses import dataclass

from .ranges import Arm, Range
from .version import Version


@dataclass(frozen=True)
class Decision:
    version: Version
    range_text: str
    arm: int | None
    reasons: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.arm is not None

    def verdict(self) -> str:
        if self.ok:
            return f"satisfies {self.range_text} (arm {self.arm})"
        return f"does not satisfy {self.range_text}"

    def lines(self) -> list[str]:
        return [
            f"version    {self.version}",
            f"range      {self.range_text}",
            f"verdict    {self.verdict()}",
            *(f"           {reason}" for reason in self.reasons),
        ]


def _bounds_reason(version: Version, arm: Arm) -> str:
    if arm.empty:
        return "this arm allows nothing"
    if arm.lower is not None and version < arm.lower:
        return f"the version is below the lower bound {arm.lower}"
    if arm.upper is not None and version > arm.upper:
        return f"the version is above the upper bound {arm.upper}"
    if arm.lower is not None and version == arm.lower and not arm.lower_inclusive:
        return f"the version equals the lower bound {arm.lower}, which is excluded"
    if arm.upper is not None and version == arm.upper and not arm.upper_inclusive:
        return f"the version equals the upper bound {arm.upper}, which is excluded"
    if version.is_prerelease:
        core = ".".join(str(part) for part in version.core)
        return (
            f"{version} is a prerelease, and no comparator in this arm names a prerelease of {core}"
        )
    return f"the version is inside {arm.bound_text()}"


def decide(version: Version, chosen: Range) -> Decision:
    reasons: list[str] = []
    for number, arm in enumerate(chosen.arms, start=1):
        reason = _bounds_reason(version, arm)
        reasons.append(f"arm {number} {arm.render()}: {reason}")
        if arm.contains(version):
            return Decision(version, chosen.text, number, tuple(reasons))
    if not reasons:
        reasons.append("the range has no arms")
    return Decision(version, chosen.text, None, tuple(reasons))
