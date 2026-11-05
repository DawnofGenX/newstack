import threading

import pytest

from {{ package_name }} import model as model_mod
from {{ package_name }}.store import Store

BODY = {"amount": 1200}


def request(key: str = "order-8f3a1c2d", amount: int = 1200) -> model_mod.Request:
    return model_mod.Request(scope="charge", key=key, body={"amount": amount})


def test_a_fresh_key_is_claimable_once(store) -> None:
    claim = store.claim(request())
    assert claim.fresh is True
    assert claim.attempt == 1
    with pytest.raises(model_mod.InProgress):
        store.claim(request())


def test_the_in_flight_refusal_carries_a_retry_hint(store) -> None:
    store.claim(request())
    with pytest.raises(model_mod.InProgress) as caught:
        store.claim(request())
    assert 0 < caught.value.retry_after_s <= 30.0


def test_a_completed_key_replays_the_stored_answer(store) -> None:
    claim = store.claim(request())
    store.complete(request(), claim.attempt, model_mod.Response(201, '{"charged": 1200}'))
    replay = store.claim(request())
    assert replay.replay is True
    assert replay.status == 201
    assert replay.body == '{"charged": 1200}'


def test_a_replay_is_byte_identical(store) -> None:
    body = '{"charged": 1200, "id": "ch_1"}'
    claim = store.claim(request())
    store.complete(request(), claim.attempt, model_mod.Response(201, body))
    assert store.claim(request()).body == body


def test_a_different_body_on_the_same_key_is_a_mismatch(store) -> None:
    store.claim(request())
    with pytest.raises(model_mod.Mismatch, match="different request"):
        store.claim(request(amount=9900))


def test_a_mismatch_is_reported_even_after_completion(store) -> None:
    claim = store.claim(request())
    store.complete(request(), claim.attempt, model_mod.Response(201, "{}"))
    with pytest.raises(model_mod.Mismatch):
        store.claim(request(amount=9900))


def test_the_lease_expiry_lets_another_attempt_take_over(store, clock) -> None:
    first = store.claim(request())
    clock.advance(31.0)
    second = store.claim(request())
    assert second.attempt == first.attempt + 1
    assert second.fresh is True


def test_a_lease_alone_does_not_fence_the_old_attempt(store, clock) -> None:
    claim = store.claim(request())
    clock.advance(31.0)
    store.complete(request(), claim.attempt, model_mod.Response(201, "{}"))
    assert store.claim(request()).replay is True


def test_the_attempt_fences_once_someone_takes_over(tmp_path, clock) -> None:
    path = tmp_path / "takeover.db"
    first = Store(path, clock=clock)
    rival = Store(path, clock=clock)
    try:
        stale = first.claim(request())
        clock.advance(31.0)
        takeover = rival.claim(request())
        with pytest.raises(model_mod.OwnerLost, match="no longer held"):
            first.complete(request(), stale.attempt, model_mod.Response(201, "{}"))
        rival.complete(request(), takeover.attempt, model_mod.Response(201, "{}"))
    finally:
        rival.close()
        first.close()


def test_releasing_a_key_makes_it_claimable_without_waiting(store) -> None:
    claim = store.claim(request())
    store.release(request(), claim.attempt)
    assert store.claim(request()).attempt == 2


def test_releasing_a_completed_key_is_refused(store) -> None:
    claim = store.claim(request())
    store.complete(request(), claim.attempt, model_mod.Response(201, "{}"))
    with pytest.raises(model_mod.OwnerLost):
        store.release(request(), claim.attempt)


def test_the_row_survives_a_restart(tmp_path, clock) -> None:
    path = tmp_path / "persist.db"
    first = Store(path, clock=clock)
    try:
        claim = first.claim(request())
        first.complete(request(), claim.attempt, model_mod.Response(202, '{"queued": true}'))
    finally:
        first.close()
    second = Store(path, clock=clock)
    try:
        replay = second.claim(request())
        assert replay.replay is True
        assert replay.status == 202
    finally:
        second.close()


def test_pruning_forgets_old_completed_keys_only(store, clock) -> None:
    old = request(key="order-old00001")
    claim = store.claim(old)
    store.complete(old, claim.attempt, model_mod.Response(201, "{}"))
    live = request(key="order-live0001")
    store.claim(live)
    clock.advance(3600.0)
    assert store.prune(60.0) == 1
    assert store.count() == 1
    assert store.count("claimed") == 1


def test_pruning_rejects_a_negative_window(store) -> None:
    with pytest.raises(ValueError, match="negative"):
        store.prune(-1.0)


def test_an_unknown_state_is_refused(store) -> None:
    with pytest.raises(ValueError, match="unknown state"):
        store.count("pending")


def test_a_lease_must_be_positive(tmp_path) -> None:
    with pytest.raises(ValueError, match="positive"):
        Store(tmp_path / "bad.db", lease_s=0)


def test_four_threads_produce_one_fresh_claim(tmp_path, clock) -> None:
    path = tmp_path / "race.db"
    started = threading.Barrier(4)
    outcomes: list[str] = []

    def worker() -> None:
        opened = Store(path, clock=clock)
        try:
            started.wait(timeout=5)
            try:
                opened.claim(request(key="order-race0001"))
                outcomes.append("claimed")
            except model_mod.InProgress:
                outcomes.append("refused")
        finally:
            opened.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert len(outcomes) == 4
    assert outcomes.count("claimed") == 1
    assert outcomes.count("refused") == 3
