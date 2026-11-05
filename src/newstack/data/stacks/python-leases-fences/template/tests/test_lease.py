from {{ package_name }} import lease as subject
from {{ package_name }}.clocks import ManualClock


def store(ttl: int = 1_000) -> tuple[subject.LeaseStore, ManualClock]:
    clock = ManualClock()
    return subject.LeaseStore(clock, ttl), clock


def test_acquire_grants_the_first_token() -> None:
    leases, _ = store()
    lease = leases.acquire("a")
    assert lease is not None
    assert lease.token == 1
    assert lease.expires_ms == 1_000


def test_a_live_lease_is_not_granted_twice() -> None:
    leases, _ = store()
    assert leases.acquire("a") is not None
    assert leases.acquire("b") is None
    assert "held by a" in leases.refusals[-1]


def test_an_expired_lease_is_granted_with_a_new_token() -> None:
    leases, clock = store()
    first = leases.acquire("a")
    assert first is not None
    clock.advance(1_000)
    second = leases.acquire("b")
    assert second is not None
    assert second.token == first.token + 1


def test_renewal_extends_from_now() -> None:
    leases, clock = store()
    lease = leases.acquire("a")
    assert lease is not None
    clock.advance(900)
    renewed = leases.renew(lease)
    assert renewed is not None
    assert renewed.expires_ms == 1_900


def test_renewal_after_expiry_is_refused() -> None:
    leases, clock = store()
    lease = leases.acquire("a")
    assert lease is not None
    clock.advance(1_001)
    assert leases.renew(lease) is None


def test_a_stale_lease_is_not_valid() -> None:
    leases, clock = store()
    first = leases.acquire("a")
    assert first is not None
    clock.advance(1_000)
    assert leases.acquire("b") is not None
    assert not leases.valid(first)


def test_release_frees_the_store() -> None:
    leases, _ = store()
    lease = leases.acquire("a")
    assert lease is not None
    assert leases.release(lease)
    assert leases.status() == "free"


def test_release_twice_is_refused() -> None:
    leases, _ = store()
    lease = leases.acquire("a")
    assert lease is not None
    assert leases.release(lease)
    assert not leases.release(lease)


def test_status_is_readable_in_every_state() -> None:
    leases, clock = store()
    assert leases.status() == "free"
    lease = leases.acquire("a")
    assert lease is not None
    assert "held by a" in leases.status()
    clock.advance(1_000)
    assert "expired" in leases.status()


def test_an_empty_holder_is_refused() -> None:
    leases, _ = store()
    try:
        leases.acquire("")
    except subject.LeaseError as error:
        assert "holder" in str(error)
    else:
        raise AssertionError("an empty holder was granted a lease")


def test_a_zero_ttl_is_refused() -> None:
    try:
        subject.LeaseStore(ManualClock(), 0)
    except subject.LeaseError as error:
        assert "at least 1" in str(error)
    else:
        raise AssertionError("a zero ttl was accepted")


def test_the_holder_clock_is_irrelevant() -> None:
    leases, clock = store()
    lease = leases.acquire("a")
    assert lease is not None
    clock.advance(1_200)
    assert subject.holder_clock_is_irrelevant(leases, lease, 500)
