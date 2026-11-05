"""The engine: buffer until the watermark passes, then speak once.

The rules, in the order they bite:

1. **A window is emitted when the watermark reaches its end**, and not before.
   The watermark is ``max(event time seen) - allowed lateness``, derived from the
   DATA, so replaying a file gives the same output regardless of how fast it was
   read. A wall-clock watermark makes yesterday's file unreproducible.
2. **Buffering is what makes lateness work.** An event that arrives after its
   window's end but before its watermark changes the aggregate, because the
   aggregate does not exist yet. A design that emits on the first event and
   patches afterwards cannot tell you which of its numbers were patched.
3. **An event whose window closed before its watermark is `too_late`.** It is
   reported with the instant, the window and the watermark that closed it, and
   it does not modify an emitted number. Silently dropping it hides a broken
   producer; silently re-opening the window makes yesterday's report differ from
   today's.
4. **Only windows with events are emitted.** A window with no events has no
   count to report, so it is listed under `missing` — a gap the reader can see —
   instead of being emitted as a zero.
5. **`mean` of no numeric values is None.** Events can carry a null measurement;
   averaging an empty set gives an undefined number, not 0.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from .events import Event, to_iso
from .windows import Window, containing, covering


class EngineError(ValueError):
    pass


class Aggregation(StrEnum):
    COUNT = "count"
    SUM = "sum"
    MEAN = "mean"


@dataclass(frozen=True, slots=True)
class Aggregate:
    window: Window
    count: int
    with_value: int
    total: Decimal | None
    minimum: Decimal | None
    maximum: Decimal | None
    mean: Decimal | None
    final: bool

    def value(self, aggregation: Aggregation) -> str:
        """The one number the caller asked for, formatted for a report."""
        if aggregation is Aggregation.COUNT:
            return str(self.count)
        if aggregation is Aggregation.SUM:
            return "-" if self.total is None else format(self.total, "f")
        return "-" if self.mean is None else format(self.mean.normalize(), "f")

    def as_dict(self) -> dict[str, object]:
        return {
            "window_start": self.window.start,
            "window_end": self.window.end,
            "count": self.count,
            "with_value": self.with_value,
            "total": None if self.total is None else str(self.total),
            "min": None if self.minimum is None else str(self.minimum),
            "max": None if self.maximum is None else str(self.maximum),
            "mean": None if self.mean is None else str(self.mean),
            "final": self.final,
        }


@dataclass(frozen=True, slots=True)
class Late:
    event: Event
    window: Window
    watermark_us: int
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "event_at": self.event.at,
            "window_start": self.window.start,
            "window_end": self.window.end,
            "watermark": to_iso(self.watermark_us),
            "reason": self.reason,
        }


@dataclass
class Report:
    aggregation: Aggregation
    width_us: int
    hop_us: int | None
    lateness_us: int
    watermark_us: int | None
    max_event_us: int | None
    windows: list[Aggregate] = field(default_factory=list)
    late: list[Late] = field(default_factory=list)

    @property
    def is_tiling(self) -> bool:
        return self.hop_us in (None, self.width_us)

    def missing(self) -> list[Window]:
        """Aligned windows inside the observed range that hold no events."""
        if not self.is_tiling or not self.windows:
            return []
        covered = {window.window.start_us for window in self.windows}
        first = min(window.window.start_us for window in self.windows)
        last = max(window.window.end_us for window in self.windows) - self.width_us
        return [
            window
            for window in covering(first, last, self.width_us)
            if window.start_us not in covered
        ]

    def as_dict(self) -> dict[str, object]:
        return {
            "aggregation": str(self.aggregation),
            "width_us": self.width_us,
            "hop_us": self.hop_us,
            "lateness_us": self.lateness_us,
            "watermark": None if self.watermark_us is None else to_iso(self.watermark_us),
            "max_event_at": None if self.max_event_us is None else to_iso(self.max_event_us),
            "windows": [window.as_dict() for window in self.windows],
            "late": [late.as_dict() for late in self.late],
            "missing": [window.label() for window in self.missing()],
        }


def _decimal(value: float | int | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


class Engine:
    """Push events in arrival order; get aggregates back as the watermark allows."""

    def __init__(
        self,
        width_us: int,
        *,
        hop_us: int | None = None,
        lateness_us: int = 0,
        aggregation: Aggregation | str = Aggregation.COUNT,
    ) -> None:
        if width_us <= 0:
            raise EngineError(f"width must be positive, got {width_us}")
        if hop_us is not None and hop_us <= 0:
            raise EngineError(f"hop must be positive, got {hop_us}")
        if hop_us is not None and hop_us > width_us:
            raise EngineError(f"hop {hop_us} is wider than width {width_us}")
        if lateness_us < 0:
            raise EngineError(f"lateness cannot be negative, got {lateness_us}")
        try:
            self.aggregation = Aggregation(aggregation)
        except ValueError:
            raise EngineError(
                f"unknown aggregation {aggregation!r}; pick one of "
                f"{', '.join(member.value for member in Aggregation)}"
            ) from None
        self.width_us = width_us
        self.hop_us = hop_us
        self.lateness_us = lateness_us
        self.max_event_us: int | None = None
        self._open: dict[int, list[float | None]] = {}
        self._emitted: list[Aggregate] = []
        self._emitted_starts: set[int] = set()
        self._late: list[Late] = []

    # -- the watermark -----------------------------------------------------

    @property
    def watermark_us(self) -> int | None:
        if self.max_event_us is None:
            return None
        return self.max_event_us - self.lateness_us

    def _windows_for(self, t_us: int) -> list[Window]:
        return containing(t_us, self.width_us, self.hop_us)

    # -- the two operations ------------------------------------------------

    def push(self, event: Event) -> list[Aggregate]:
        """Add one event and return any windows the watermark just closed."""
        windows = self._windows_for(event.t_us)
        # The watermark moves on the maximum event time, before the event is
        # placed: an event far in the past can itself close windows, and it must
        # be judged against the watermark its arrival created.
        if self.max_event_us is None or event.t_us > self.max_event_us:
            self.max_event_us = event.t_us
        watermark = self.watermark_us
        assert watermark is not None
        for window in windows:
            if window.end_us <= watermark:
                if window.start_us in self._emitted_starts:
                    reason = "the window had already been emitted"
                else:
                    reason = "the window closed before this event's arrival"
                self._late.append(
                    Late(
                        event=event,
                        window=window,
                        watermark_us=watermark,
                        reason=f"{reason}: window ended {window.end}, watermark is "
                        f"{to_iso(watermark)}",
                    )
                )
                continue
            self._open.setdefault(window.start_us, []).append(event.value)
        return self._emit_ready(by_watermark=True)

    def _emit_ready(self, *, by_watermark: bool) -> list[Aggregate]:
        watermark = self.watermark_us
        if watermark is None:
            return []
        # A watermark emission only closes windows the watermark reached; a
        # flush emits everything still buffered, because the input ended.
        closed = [
            start
            for start in self._open
            if not by_watermark or start + self.width_us <= watermark
        ]
        emitted: list[Aggregate] = []
        for start in sorted(closed):
            values = self._open.pop(start)
            aggregate = self._aggregate(
                Window(start, start + self.width_us), values, final=by_watermark
            )
            self._emitted.append(aggregate)
            self._emitted_starts.add(start)
            emitted.append(aggregate)
        return emitted

    def flush(self) -> list[Aggregate]:
        """Emit what is still buffered, marked ``final: false``.

        A flushed aggregate is emitted because the input ended, not because the
        watermark reached it, so its window is still open to late events. Calling
        it final would be a claim about the future.
        """
        return self._emit_ready(by_watermark=False)

    def _aggregate(self, window: Window, values: list[float | None], *, final: bool) -> Aggregate:
        numbers = [number for number in (_decimal(value) for value in values) if number is not None]
        total = sum(numbers, Decimal(0)) if numbers else None
        mean = None if not numbers else total / len(numbers)  # type: ignore[operator]
        return Aggregate(
            window=window,
            count=len(values),
            with_value=len(numbers),
            total=total,
            minimum=min(numbers) if numbers else None,
            maximum=max(numbers) if numbers else None,
            mean=mean,
            final=final,
        )

    def report(self) -> Report:
        windows = list(self._emitted)
        return Report(
            aggregation=self.aggregation,
            width_us=self.width_us,
            hop_us=self.hop_us,
            lateness_us=self.lateness_us,
            watermark_us=self.watermark_us,
            max_event_us=self.max_event_us,
            windows=sorted(windows, key=lambda aggregate: aggregate.window.start_us),
            late=list(self._late),
        )


def run(
    events: list[Event],
    *,
    width_us: int,
    hop_us: int | None = None,
    lateness_us: int = 0,
    aggregation: Aggregation | str = Aggregation.COUNT,
) -> Report:
    engine = Engine(
        width_us, hop_us=hop_us, lateness_us=lateness_us, aggregation=aggregation
    )
    for event in events:
        engine.push(event)
    engine.flush()
    return engine.report()
