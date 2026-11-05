"""An SLO is a target and a window; a budget is the number of bad events it allows.

Both halves are exact integers: the target is parts per million, the window is
seconds, and every comparison happens in `Decimal`, because "99.9% of a million
requests" is 1 000 events and a float will eventually tell you it is 999.9999.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

PARTS = 1_000_000
TARGET = re.compile(r"^(?P<whole>[0-9]{1,3})(?:\.(?P<fraction>[0-9]{1,6}))?%?$")
DURATION = re.compile(r"^(?P<count>[0-9]+)(?P<unit>[smhdw])$")
UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


class SloError(ValueError):
    """A target or window that cannot mean anything."""


def parse_target(text: str) -> int:
    """'99.9' or '99.9%' -> 999000 parts per million."""
    match = TARGET.match(text.strip())
    if not match:
        raise SloError(f"{text!r} is not a percentage with up to six decimals, e.g. 99.9 or 99.99%")
    whole = int(match.group("whole"))
    fraction = (match.group("fraction") or "0").ljust(6, "0")
    # Six decimals of a percent is hundred-thousandths of the whole, so the
    # scaled integer divides by 100 exactly and never touches a float.
    ppm = (whole * PARTS + int(fraction)) // 100
    if not 0 < ppm <= PARTS:
        raise SloError(f"a target must be greater than 0% and at most 100%, got {text!r}")
    return ppm


def parse_duration(text: str) -> int:
    """'30d', '90m', '6h' -> seconds. One unit per value, on purpose."""
    match = DURATION.match(text.strip())
    if not match:
        raise SloError(f"{text!r} is not a duration like 90s, 30m, 6h, 30d or 4w")
    count = int(match.group("count"))
    if count == 0:
        raise SloError(f"{text!r} has no duration in it")
    return count * UNITS[match.group("unit")]


@dataclass(frozen=True)
class Slo:
    target_ppm: int
    window_s: int

    @property
    def allowed_ppm(self) -> int:
        return PARTS - self.target_ppm

    @property
    def allowed_fraction(self) -> Decimal:
        return Decimal(self.allowed_ppm) / Decimal(PARTS)

    @property
    def target_text(self) -> str:
        percent = Decimal(self.target_ppm) * 100 / PARTS
        return f"{percent.normalize():f}%"

    def allowed_bad(self, total_events: int) -> Decimal:
        """How many bad events the budget allows inside this many events."""
        return self.allowed_fraction * Decimal(total_events)

    def as_dict(self) -> dict[str, object]:
        return {
            "target": self.target_text,
            "target_ppm": self.target_ppm,
            "allowed_ppm": self.allowed_ppm,
            "window_s": self.window_s,
        }


def slo_of(target: str | int, window: str | int) -> Slo:
    ppm = target if isinstance(target, int) else parse_target(target)
    seconds = window if isinstance(window, int) else parse_duration(window)
    if not 0 < ppm <= PARTS:
        raise SloError(f"a target must be greater than 0% and at most 100%, got {ppm} ppm")
    if seconds < 1:
        raise SloError(f"a window must be at least 1 second, got {seconds}")
    return Slo(ppm, seconds)
