import pytest

from {{ package_name }} import guard as guard_mod
from {{ package_name }} import model as model_mod
from {{ package_name }}.store import Store


def request(key: str = "order-8f3a1c2d") -> model_mod.Request:
    return model_mod.Request(scope="charge", key=key, body={"amount": 1200})


def test_the_handler_runs_once_and_the_second_call_replays(store) -> None:
    calls: list[str] = []

    def handler(one: model_mod.Request) -> model_mod.Response:
        calls.append(one.key)
        return model_mod.Response(201, '{"charged": 1200}')

    first = guard_mod.execute(store, request(), handler)
    second = guard_mod.execute(store, request(), handler)
    assert first.executed is True
    assert second.replay is True
    assert calls == ["order-8f3a1c2d"]


def test_the_replayed_body_is_the_one_the_handler_returned(store) -> None:
    def handler(one: model_mod.Request) -> model_mod.Response:
        return model_mod.Response(201, '{"charged": 1200, "id": "ch_9"}')

    guard_mod.execute(store, request(), handler)
    again = guard_mod.execute(store, request(), handler)
    assert again.body == '{"charged": 1200, "id": "ch_9"}'
    assert again.status == 201


def test_a_raising_handler_releases_the_key(store) -> None:
    def broken(one: model_mod.Request) -> model_mod.Response:
        raise RuntimeError("provider said no")

    with pytest.raises(RuntimeError, match="provider said no"):
        guard_mod.execute(store, request(), broken)
    outcome = guard_mod.execute(store, request(), lambda one: model_mod.Response(201, "{}"))
    assert outcome.attempts == 2


def test_a_handler_slower_than_the_lease_loses_its_row(tmp_path, clock) -> None:
    path = tmp_path / "slow.db"
    mine = Store(path, clock=clock)
    rival = Store(path, clock=clock)
    try:

        def slow(one: model_mod.Request) -> model_mod.Response:
            clock.advance(31.0)
            rival.claim(one)
            return model_mod.Response(201, "{}")

        with pytest.raises(model_mod.OwnerLost):
            guard_mod.execute(mine, request(), slow, lease_s=30.0)
    finally:
        rival.close()
        mine.close()


def test_a_short_lease_is_honoured(store) -> None:
    claim = store.claim(request(), lease_s=0.5)
    assert claim.attempt == 1
