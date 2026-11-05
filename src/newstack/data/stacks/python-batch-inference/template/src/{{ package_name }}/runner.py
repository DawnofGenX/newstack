"""Fan requests out over a bounded thread pool and record each outcome."""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from {{ package_name }}.client import ChatClient, RequestFailed
from {{ package_name }}.records import Request, Result, ResultWriter


@dataclass
class Summary:
    """Counts for the run, including what was skipped because it was already done."""

    total: int = 0
    ok: int = 0
    failed: int = 0
    resumed: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def worked(self) -> int:
        """Requests this run actually sent."""
        return self.ok + self.failed

    def lines(self) -> list[str]:
        """Human-readable summary, one number per line so `grep` works in CI."""
        rows = [
            f"requests  {self.total}",
            f"ok        {self.ok}",
            f"failed    {self.failed}",
            f"resumed   {self.resumed}",
            f"tokens_in {self.tokens_in}",
            f"tokens_out {self.tokens_out}",
        ]
        rows.extend(f"failure   {name}" for name in self.failures)
        return rows


def one(client: ChatClient, request: Request) -> Result:
    """Ask for one answer and turn any failure into a record, never an exception."""
    try:
        output, tokens_in, tokens_out, attempts = client.complete(request.prompt)
    except RequestFailed as exc:
        return Result(id=request.id, attempts=0, ok=False, error=str(exc))
    return Result(
        id=request.id,
        output=output,
        model=client.model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        attempts=attempts,
    )


def run(
    pending: Sequence[Request],
    client: ChatClient,
    writer: ResultWriter,
    *,
    concurrency: int = 4,
    total: int | None = None,
    resumed: int = 0,
) -> Summary:
    """Run ``pending`` with at most ``concurrency`` requests in flight."""
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")
    summary = Summary(total=len(pending) if total is None else total, resumed=resumed)
    if not pending:
        return summary
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(one, client, request): request for request in pending}
        for future in as_completed(futures):
            result = future.result()
            writer.write(result)
            if result.ok:
                summary.ok += 1
                summary.tokens_in += result.tokens_in
                summary.tokens_out += result.tokens_out
            else:
                summary.failed += 1
                summary.failures.append(f"{result.id}: {result.error}")
    return summary
