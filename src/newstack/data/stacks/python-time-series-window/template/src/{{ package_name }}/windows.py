"""Windows are half-open intervals aligned to the epoch, and that is the whole design.

An interval aligned to the first event makes the answer depend on which event
arrived first: replay the same day with one extra sample at the front and every
boundary moves. Aligning to epoch multiples means 10:00:07 with a 60s width lands
in 10:00:00..10:01:00 no matter what else is in the file.
"""

from __future__ import annotations

from dataclasses import dataclass

from .events import to_iso


class WindowError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Window:
    """A half-open interval ``[start_us, end_us)``."""

    start_us: int
    end_us: int

    def __post_init__(self) -> None:
        if self.end_us <= self.start_us:
            raise WindowError(
                f"window {self.start_us}..{self.end_us} is empty or inverted; "
                "a half-open interval needs end > start"
            )

    def __contains__(self, t_us: object) -> bool:
        return isinstance(t_us, int) and self.start_us <= t_us < self.end_us

    @property
    def width_us(self) -> int:
        return self.end_us - self.start_us

    @property
    def start(self) -> str:
        return to_iso(self.start_us)

    @property
    def end(self) -> str:
        return to_iso(self.end_us)

    def label(self) -> str:
        return f"{self.start}..{self.end}"

    def intersects(self, other: Window) -> bool:
        return self.start_us < other.end_us and other.start_us < self.end_us


def align(t_us: int, width_us: int) -> int:
    """The start of the aligned window containing ``t_us``."""
    if width_us <= 0:
        raise WindowError(f"width must be positive, got {width_us}")
    return (t_us // width_us) * width_us


def containing(t_us: int, width_us: int, hop_us: int | None = None) -> list[Window]:
    """Every window that contains ``t_us``.

    With ``hop_us is None`` the windows tile the timeline and exactly one
    contains the instant. With a hop, windows overlap and an event belongs to
    each of them — counting it once would make a sliding aggregate disagree with
    the tumbling one for no stated reason.
    """
    if hop_us is None:
        start = align(t_us, width_us)
        return [Window(start, start + width_us)]
    if hop_us <= 0:
        raise WindowError(f"hop must be positive, got {hop_us}")
    if hop_us > width_us:
        raise WindowError(
            f"hop {hop_us} is wider than the window {width_us}: that leaves instants "
            "in no window at all, and the gap is invisible in the output"
        )
    # The newest window that can still contain t starts at floor(t / hop) * hop;
    # older ones start one hop earlier each, down to width - hop back.
    newest = (t_us // hop_us) * hop_us
    found: list[Window] = []
    for k in range(0, width_us // hop_us):
        start = newest - k * hop_us
        window = Window(start, start + width_us)
        if t_us in window:
            found.append(window)
    return sorted(found, key=lambda window: window.start_us)


def covering(first_us: int, last_us: int, width_us: int) -> list[Window]:
    """The aligned tiling that spans the two instants, inclusive."""
    if last_us < first_us:
        raise WindowError(f"last {last_us} is before first {first_us}")
    start = align(first_us, width_us)
    windows: list[Window] = []
    while start <= last_us:
        windows.append(Window(start, start + width_us))
        start += width_us
    return windows
