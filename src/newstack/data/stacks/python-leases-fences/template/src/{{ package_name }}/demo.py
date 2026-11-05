"""Six stories, each one a lease that expired while its holder was not looking."""

from __future__ import annotations

from dataclasses import dataclass

from .clocks import ManualClock
from .fence import FencedValue, UnfencedValue, attempt
from .lease import LeaseStore, holder_clock_is_irrelevant

TTL_MS = 1_000


@dataclass
class Step:
    at_ms: int
    event: str
    detail: str

    def line(self) -> str:
        return f"  {self.at_ms:>5}  {self.event:<26} {self.detail}"


def pause_story() -> tuple[str, list[str], bool]:
    """A holder pauses past its lease and writes anyway."""
    clock = ManualClock()
    store = LeaseStore(clock, TTL_MS)
    fenced, unfenced = FencedValue(value="initial"), UnfencedValue(value="initial")
    steps: list[Step] = []

    first = store.acquire("worker-a")
    assert first is not None
    steps.append(Step(clock.now_ms(), "worker-a acquires", first.text()))

    clock.advance(1_500)  # worker-a is suspended and never learns
    steps.append(Step(clock.now_ms(), "clock passes the deadline", store.status()))

    second = store.acquire("worker-b")
    assert second is not None
    steps.append(Step(clock.now_ms(), "worker-b acquires", second.text()))
    steps.append(Step(clock.now_ms(), "worker-b writes", attempt(fenced, second.token, "b-1")))
    steps.append(Step(clock.now_ms(), "fenced resource", attempt(fenced, first.token, "a-late")))
    ghost = attempt(unfenced, first.token, "a-late")
    steps.append(Step(clock.now_ms(), "unfenced resource", ghost))

    kept = fenced.value == "b-1"
    lost = unfenced.value == "a-late"
    title = "1. a lease alone cannot stop a paused holder; a token can"
    body = [
        "  the pause is the whole story: worker-a believed it had time left",
        *[step.line() for step in steps],
        f"  fenced value after the ghost write   {fenced.value!r}",
        f"  unfenced value after the same write  {unfenced.value!r}",
        "  the second line is a lost update: the resource had no way to tell",
    ]
    return title, body, kept and lost


def renewal_story() -> tuple[str, list[str], bool]:
    """Renewal extends from now, so a pause is not banked."""
    clock = ManualClock()
    store = LeaseStore(clock, TTL_MS)
    lease = store.acquire("worker-a")
    assert lease is not None
    clock.advance(900)
    renewed = store.renew(lease)
    assert renewed is not None
    body = [
        f"  acquire at 0       {lease.text()}",
        f"  renew at 900       {renewed.text()}",
        "  renewal extends from NOW: 900 + 1000 = 1900",
        "  extending from the old expiry would have given 1000 + 1000 = 2000,",
        "  which pays a paused holder for time it never used",
    ]
    expired_at = renewed.expires_ms
    return "2. renewal is measured from now, not from the old deadline", body, expired_at == 1_900


def pause_ends_story() -> tuple[str, list[str], bool]:
    clock = ManualClock()
    store = LeaseStore(clock, TTL_MS)
    lease = store.acquire("worker-a")
    assert lease is not None
    clock.advance(1_001)
    refused = store.renew(lease)
    body = [
        f"  acquire at 0       {lease.text()}",
        f"  renew at 1001      {'refused' if refused is None else refused.text()}",
        f"  status             {store.status()}",
        "  the store's clock decides, and it says the lease is gone",
    ]
    title = "3. a pause past the deadline ends the lease, no matter what the holder thinks"
    return title, body, refused is None


def clock_story() -> tuple[str, list[str], bool]:
    clock = ManualClock()
    store = LeaseStore(clock, TTL_MS)
    lease = store.acquire("worker-a")
    assert lease is not None
    clock.advance(1_200)
    theirs = 500  # worker-a's clock is slow by 700 ms
    ignored = holder_clock_is_irrelevant(store, lease, theirs)
    body = [
        "  store now          1200",
        f"  holder's clock     {theirs}",
        f"  holder thinks valid {lease.valid_at(theirs)}",
        f"  store says valid    {store.valid(lease)}",
        "  a lease checked against the holder's own clock is a wish, not a lock",
    ]
    return "4. the store's clock is the authority; the holder's is advisory", body, ignored


def release_story() -> tuple[str, list[str], bool]:
    clock = ManualClock()
    store = LeaseStore(clock, TTL_MS)
    first = store.acquire("worker-a")
    assert first is not None
    released = store.release(first)
    second = store.acquire("worker-b")
    assert second is not None
    body = [
        f"  worker-a           {first.text()}",
        f"  release            {released}",
        f"  worker-b           {second.text()}",
        f"  old token writes   {attempt(FencedValue(), first.token, 'a-late')}",
        "  a handover is a new token, never a reused one",
    ]
    return "5. a release hands over with a fresh token", body, second.token > first.token


def many_writes_story() -> tuple[str, list[str], bool]:
    clock = ManualClock()
    store = LeaseStore(clock, TTL_MS)
    lease = store.acquire("worker-a")
    assert lease is not None
    value = FencedValue()
    results = [attempt(value, lease.token, f"a-{number}") for number in range(3)]
    body = [
        f"  one lease, token {lease.token}",
        *[f"  write {number}         {result}" for number, result in enumerate(results)],
        f"  writes accepted    {value.writes}",
        "  the fence compares tokens, it does not stop a holder from working",
    ]
    title = "6. one token may write many times: the fence is a monotonic check"
    return title, body, value.writes == 3


def stories() -> list[tuple[str, list[str], bool]]:
    return [
        pause_story(),
        renewal_story(),
        pause_ends_story(),
        clock_story(),
        release_story(),
        many_writes_story(),
    ]


def render() -> str:
    lines: list[str] = []
    for title, body, _ in stories():
        lines.append(title)
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def timeline(ttl_ms: int = TTL_MS, pause_ms: int = 1_500) -> tuple[list[str], bool]:
    """The full pause scenario as a table, with the contract checked at the end."""
    if pause_ms <= ttl_ms:
        raise ValueError(
            f"a pause of {pause_ms} ms inside a {ttl_ms} ms lease never expires: nothing to show"
        )
    clock = ManualClock()
    store = LeaseStore(clock, ttl_ms)
    fenced = FencedValue(value="initial")
    rows: list[str] = ["   time  event                      detail"]
    first = store.acquire("worker-a")
    assert first is not None
    rows.append(f"  {clock.now_ms():>5}  {'acquire worker-a':<26} {first.text()}")
    clock.advance(pause_ms)
    rows.append(f"  {clock.now_ms():>5}  {'deadline passes':<26} {store.status()}")
    second = store.acquire("worker-b")
    assert second is not None
    rows.append(f"  {clock.now_ms():>5}  {'acquire worker-b':<26} {second.text()}")
    rows.append(f"  {clock.now_ms():>5}  {'write with token 2':<26} {attempt(fenced, 2, 'b')}")
    rows.append(f"  {clock.now_ms():>5}  {'write with token 1':<26} {attempt(fenced, 1, 'a')}")
    rows.append(f"  {clock.now_ms():>5}  {'value':<26} {fenced.value!r}")
    contract = fenced.value == "b" and fenced.token == 2
    rows.append(f"  {'':>5}  {'contract':<26} {'kept' if contract else 'BROKEN'}")
    return rows, contract
