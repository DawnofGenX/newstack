"""Check the lease and the fence against the failures they exist for."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

from .cli import EXIT_OK, EXIT_UNUSABLE, main
from .clocks import ClockError, ManualClock
from .demo import pause_story, renewal_story, stories
from .fence import FencedValue, StaleToken, UnfencedValue, attempt
from .lease import LeaseError, LeaseStore, holder_clock_is_irrelevant

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))


def refuses(name: str, kind: type[BaseException], call, needle: str = "") -> None:
    try:
        call()
    except kind as error:
        check(name, needle in str(error), f"message: {error}")
    except BaseException as error:  # a wrong exception type is a failure too
        check(name, False, f"raised {type(error).__name__}, expected {kind.__name__}")
    else:
        check(name, False, "nothing was raised")


def quiet(argv: list[str]) -> tuple[int, str]:
    """Run the CLI with both streams captured. argparse's own exits become codes."""
    out = io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = main(argv)
    except SystemExit as stop:  # argparse exits 2 on a missing command
        code = stop.code if isinstance(stop.code, int) else 2
    return code, out.getvalue()


def run() -> int:
    CHECKS.clear()

    # -- clocks ---------------------------------------------------------------------
    clock = ManualClock(100)
    check("a clock reads what it was set to", clock.now_ms() == 100)
    check("advancing returns the new time", clock.advance(50) == 150)
    refuses("a clock cannot start negative", ClockError, lambda: ManualClock(-1))
    refuses("time does not run backwards", ClockError, lambda: clock.advance(-1))

    # -- lease ----------------------------------------------------------------------
    store = LeaseStore(ManualClock(), 1_000)
    lease = store.acquire("a")
    check("the first acquire succeeds", lease is not None)
    assert lease is not None
    check("the first token is 1", lease.token == 1)
    check("the deadline is now plus the ttl", lease.expires_ms == 1_000)
    check("a second holder is refused while the lease is live", store.acquire("b") is None)
    check("the refusal names the holder", "held by a" in store.refusals[-1])
    check("the lease is valid at its start", store.valid(lease))
    refuses("an empty holder is refused", LeaseError, lambda: store.acquire(""))
    refuses("a zero ttl is refused", LeaseError, lambda: LeaseStore(ManualClock(), 0))

    renewed = store.renew(lease)
    check("renewal returns a lease", renewed is not None)
    assert renewed is not None
    check("renewal keeps the token", renewed.token == lease.token)
    check("renewal extends from now", renewed.expires_ms == 1_000)

    clock = ManualClock()
    store = LeaseStore(clock, 1_000)
    first = store.acquire("a")
    assert first is not None
    clock.advance(900)
    renewed = store.renew(first)
    assert renewed is not None
    check("a late renewal does not bank unused time", renewed.expires_ms == 1_900)
    clock.advance(1_101)
    check("the renewed lease expires on time", not store.valid(renewed))
    check("renewal after expiry is refused", store.renew(renewed) is None)
    check("an expired lease can be taken", store.acquire("b") is not None)
    check("the new token is larger", store.last_token == 2)

    # -- handover -------------------------------------------------------------------
    clock = ManualClock()
    store = LeaseStore(clock, 1_000)
    lease = store.acquire("a")
    assert lease is not None
    check("release succeeds for the holder", store.release(lease))
    check("the store is free after release", store.status() == "free")
    check("release twice is refused", not store.release(lease))
    second = store.acquire("b")
    assert second is not None
    check("a handover issues a new token", second.token == lease.token + 1)
    check("the old lease is not valid", not store.valid(lease))

    # -- fence ----------------------------------------------------------------------
    value = FencedValue()
    value.write(1, "one")
    check("a first write is accepted", value.value == "one")
    value.write(1, "again")
    check("one token may write twice", value.writes == 2)
    refuses("an older token is refused", StaleToken, lambda: value.write(0, "late"))
    stale = _last_error(lambda: value.write(0, "x"))
    check("the refusal names both tokens", "token 0 is older" in str(stale))
    value.write(2, "two")
    check("a newer token takes over", value.value == "two")
    check("the write history is kept", [token for token, _ in value.history] == [1, 1, 2])
    unfenced = UnfencedValue()
    unfenced.write(2, "b")
    unfenced.write(1, "a")
    check("an unfenced resource keeps the ghost write", unfenced.value == "a")
    check("attempt reports a refusal", attempt(value, 1, "x").startswith("refused"))
    check("attempt reports an acceptance", attempt(value, 3, "x").startswith("accepted"))

    # -- clock authority ------------------------------------------------------------
    clock = ManualClock()
    store = LeaseStore(clock, 1_000)
    lease = store.acquire("a")
    assert lease is not None
    clock.advance(1_200)
    ignored = holder_clock_is_irrelevant(store, lease, 500)
    check("a holder's clock cannot keep a lease alive", ignored)
    fresh = LeaseStore(ManualClock(), 1_000)
    live = fresh.acquire("a")
    assert live is not None
    check("a live lease is not called irrelevant", not holder_clock_is_irrelevant(fresh, live, 500))

    # -- demo -----------------------------------------------------------------------
    for title, _, held in stories():
        check(f"story holds: {title[:40]}", held)
    check("each story has a body", all(len(body) >= 3 for _, body, _ in stories()))
    check("the pause story reports the kept contract", pause_story()[2])
    check("renewal story holds", renewal_story()[2])

    # -- cli ------------------------------------------------------------------------
    code, out = quiet(["demo"])
    check("demo exits 0", code == EXIT_OK, f"code {code}")
    check("demo prints six stories", out.count("\n") > 10 and "6. " in out)
    code, out = quiet(["model"])
    check("model exits 0 on a working scenario", code == EXIT_OK, f"code {code}")
    check("model prints the contract", "contract" in out and "kept" in out)
    code, _ = quiet(["model", "--ttl-ms", "1000", "--pause-ms", "500"])
    check("model refuses a pause inside the lease", code == EXIT_UNUSABLE, f"code {code}")
    code, _ = quiet(["model", "--ttl-ms", "0"])
    check("model refuses a zero ttl", code == EXIT_UNUSABLE, f"code {code}")
    code, _ = quiet([])
    check("a missing command is a usage error", code == 2, f"code {code}")

    passed = sum(1 for _, held, _ in CHECKS if held)
    for name, held, detail in CHECKS:
        if not held:
            print(f"FAIL {name}: {detail}")
    print(f"selftest: {passed} of {len(CHECKS)} checks passed")
    return 0 if passed == len(CHECKS) else 1


def _last_error(call) -> BaseException:
    try:
        call()
    except BaseException as error:  # the message is the point
        return error
    raise AssertionError("nothing was raised")
