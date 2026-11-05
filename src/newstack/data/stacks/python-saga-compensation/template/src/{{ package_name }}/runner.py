"""Run a saga forward, and on failure unwind it backwards.

A saga is a sequence of local transactions with a compensating action each. The
rules this runner enforces are the ones that survive an audit:

* compensations run in the reverse of the order the steps completed, so a
  dependency is never torn down before the thing that needs it;
* a compensation that keeps failing does not stop the others -- leaving later
  compensations unattempted because an earlier one broke turns a bad day into a
  lost afternoon, so the runner records the failure and keeps unwinding;
* a step that succeeded but declares no compensation makes the rollback
  *incomplete*, not "rolled back": pretending an irreversible charge was undone
  is the single most expensive lie this file could tell;
* re-running a journaled saga is a no-op, and an interrupted step (``started``
  with no outcome) is retried with the same idempotency key rather than assumed
  to have worked.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .journal import Journal

COMPLETED = "completed"
ROLLED_BACK = "rolled_back"
INCOMPLETE = "incomplete"


class SagaError(RuntimeError):
    """The saga is not configured in a way that can be run."""


@dataclass
class Context:
    saga: str
    step: str
    key: str
    attempt: int
    state: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> str:
        return f"{self.saga}/{self.step} (attempt {self.attempt}, key {self.key})"


@dataclass(frozen=True)
class Step:
    name: str
    action: Callable[[Context], Any]
    compensation: Callable[[Context], Any] | None = None
    max_attempts: int = 1
    retry_on: tuple[type[Exception], ...] = ()

    def __post_init__(self) -> None:
        if not self.name or "/" in self.name or ":" in self.name:
            raise SagaError(f"step name {self.name!r} must be non-empty and contain no ':' or '/'")
        if self.max_attempts < 1:
            raise SagaError(f"step {self.name!r} needs max_attempts >= 1")
        if self.compensation is None and self.max_attempts > 1:
            # Not a bug, just usually a misunderstanding: retrying a forward step
            # is only safe when its idempotency key is honoured.
            return


@dataclass
class Outcome:
    saga: str
    status: str
    failed_step: str | None
    statuses: dict[str, str]
    unrecoverable: list[str]
    records: int
    resumed: bool

    @property
    def ok(self) -> bool:
        return self.status == COMPLETED

    def lines(self) -> list[str]:
        lines = [f"saga       {self.saga}", f"status     {self.status}"]
        if self.failed_step:
            lines.append(f"failed     {self.failed_step}")
        for name, status in self.statuses.items():
            lines.append(f"step       {name:<20} {status}")
        for note in self.unrecoverable:
            lines.append(f"left       {note}")
        if self.resumed:
            lines.append("resumed    yes, from the journal")
        lines.append(f"journal    {self.records} record(s)")
        return lines

    def as_dict(self) -> dict[str, Any]:
        return {
            "saga": self.saga,
            "status": self.status,
            "failed_step": self.failed_step,
            "steps": self.statuses,
            "unrecoverable": self.unrecoverable,
            "records": self.records,
            "resumed": self.resumed,
        }


class Saga:
    def __init__(
        self,
        saga_id: str,
        steps: Sequence[Step],
        journal_path: str | Path,
        state: dict[str, Any] | None = None,
    ) -> None:
        if not saga_id or "/" in saga_id:
            raise SagaError(f"saga id {saga_id!r} must be non-empty and contain no '/'")
        if not steps:
            raise SagaError("a saga with no steps has nothing to run and nothing to undo")
        names = [step.name for step in steps]
        duplicates = {name for name in names if names.count(name) > 1}
        if duplicates:
            raise SagaError(
                f"duplicate step name(s) {sorted(duplicates)}: the journal keys steps by name, "
                "so two steps called the same thing are indistinguishable after a restart"
            )
        self.id = saga_id
        self.steps = tuple(steps)
        self.state = dict(state or {})
        self.journal = Journal(journal_path)

    def key(self, step: str) -> str:
        return f"{self.id}:{step}"

    def run(self) -> Outcome:
        recorded = self.journal.outcome(self.id)
        statuses = self.journal.statuses(self.id)
        if recorded is not None:
            return Outcome(
                saga=self.id,
                status=recorded,
                failed_step=self._failed_step(),
                statuses=statuses,
                unrecoverable=self._unrecoverable(),
                records=len(self.journal.records),
                resumed=True,
            )

        resumed = bool(statuses)
        if not resumed:
            self.journal.append(self.id, "saga.started", steps=[step.name for step in self.steps])

        # A saga that has already compensated one step is in rollback: resuming it
        # forward would re-do work on top of a partially dismantled world.
        if any(status in ("compensated", "compensation_failed") for status in statuses.values()):
            return self._finish_rollback(statuses, resumed=resumed)

        failed: str | None = None
        for step in self.steps:
            status = statuses.get(step.name)
            if status == "succeeded":
                continue
            if status == "interrupted":
                self.journal.append(
                    self.id, "step.retried", step=step.name, key=self.key(step.name)
                )
            error = self._attempt(step)
            if error is None:
                statuses[step.name] = "succeeded"
                continue
            statuses[step.name] = "failed"
            failed = step.name
            break

        if failed is None:
            self.journal.append(self.id, "saga.completed", steps=len(self.steps))
            return Outcome(
                saga=self.id,
                status=COMPLETED,
                failed_step=None,
                statuses=statuses,
                unrecoverable=[],
                records=len(self.journal.records),
                resumed=resumed,
            )
        return self._finish_rollback(statuses, resumed=resumed, failed=failed)

    def _attempt(self, step: Step) -> Exception | None:
        context = Context(
            saga=self.id,
            step=step.name,
            key=self.key(step.name),
            attempt=1,
            state=self.state,
        )
        error: Exception | None = None
        for attempt in range(1, step.max_attempts + 1):
            context.attempt = attempt
            self.journal.append(
                self.id, "step.started", step=step.name, key=context.key, attempt=attempt
            )
            try:
                step.action(context)
            except Exception as failure:
                error = failure
                retryable = attempt < step.max_attempts and (
                    not step.retry_on or isinstance(failure, step.retry_on)
                )
                self.journal.append(
                    self.id,
                    "step.failed",
                    step=step.name,
                    attempt=attempt,
                    retryable=retryable,
                    detail=f"{type(failure).__name__}: {failure}",
                )
                if not retryable:
                    return failure
                continue
            self.journal.append(
                self.id, "step.succeeded", step=step.name, key=context.key, attempt=attempt
            )
            return None
        return error

    def _compensate(self, step: Step) -> bool:
        assert step.compensation is not None
        context = Context(
            saga=self.id,
            step=step.name,
            key=self.key(step.name),
            attempt=1,
            state=self.state,
        )
        for attempt in range(1, step.max_attempts + 1):
            context.attempt = attempt
            try:
                step.compensation(context)
            except Exception as failure:
                last = f"{type(failure).__name__}: {failure}"
                self.journal.append(
                    self.id,
                    "step.compensation_failed",
                    step=step.name,
                    attempt=attempt,
                    detail=last,
                )
                continue
            self.journal.append(
                self.id, "step.compensated", step=step.name, attempt=attempt, key=context.key
            )
            return True
        return False

    def _finish_rollback(
        self,
        statuses: dict[str, str],
        *,
        resumed: bool,
        failed: str | None = None,
    ) -> Outcome:
        unrecoverable: list[str] = []
        for step in reversed(self.steps):
            if statuses.get(step.name) != "succeeded":
                continue
            if step.compensation is None:
                self.journal.append(
                    self.id,
                    "step.unrecoverable",
                    step=step.name,
                    detail="the step succeeded and declares no compensation",
                )
                statuses[step.name] = "unrecoverable"
                unrecoverable.append(f"{step.name}: no compensation was declared")
                continue
            if self._compensate(step):
                statuses[step.name] = "compensated"
            else:
                statuses[step.name] = "compensation_failed"
                unrecoverable.append(f"{step.name}: every compensation attempt failed")

        event = "saga.rolled_back" if not unrecoverable else "saga.incomplete"
        self.journal.append(self.id, event, unrecoverable=unrecoverable)
        return Outcome(
            saga=self.id,
            status=ROLLED_BACK if not unrecoverable else INCOMPLETE,
            failed_step=failed or self._failed_step(),
            statuses=statuses,
            unrecoverable=unrecoverable,
            records=len(self.journal.records),
            resumed=resumed,
        )

    def _failed_step(self) -> str | None:
        for step in self.steps:
            if self.journal.statuses(self.id).get(step.name) == "failed":
                return step.name
        return None

    def _unrecoverable(self) -> list[str]:
        statuses = self.journal.statuses(self.id)
        return [
            f"{name}: {status}"
            for name, status in statuses.items()
            if status in ("unrecoverable", "compensation_failed")
        ]
