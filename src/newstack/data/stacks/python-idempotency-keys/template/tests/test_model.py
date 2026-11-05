import json

import pytest

from {{ package_name }} import model as model_mod

BODY = {"amount": 1200, "currency": "USD"}


def test_a_fingerprint_ignores_key_order() -> None:
    reordered = {"currency": "USD", "amount": 1200}
    assert model_mod.fingerprint_of("charge", BODY) == model_mod.fingerprint_of("charge", reordered)


def test_a_fingerprint_ignores_whitespace() -> None:
    pretty = json.loads(json.dumps(BODY, indent=4))
    assert model_mod.fingerprint_of("charge", pretty) == model_mod.fingerprint_of("charge", BODY)


def test_the_scope_is_part_of_the_fingerprint() -> None:
    assert model_mod.fingerprint_of("charge", BODY) != model_mod.fingerprint_of("refund", BODY)


def test_the_fingerprint_is_sixteen_hex_characters() -> None:
    fingerprint = model_mod.fingerprint_of("charge", BODY)
    assert len(fingerprint) == 16
    assert int(fingerprint, 16) >= 0


@pytest.mark.parametrize("key", ["short", "", "order 8f3a1c2d", "order/8f3a1c2d", "a" * 129])
def test_keys_that_cannot_be_told_apart_are_refused(key: str) -> None:
    with pytest.raises(model_mod.InputError):
        model_mod.Request(scope="charge", key=key, body=BODY)


@pytest.mark.parametrize("key", ["order-8f3a1c2d", "A" * 8, "a" * 128, "x_9-Zabc"])
def test_reasonable_keys_are_accepted(key: str) -> None:
    assert model_mod.Request(scope="charge", key=key, body=BODY).key == key


def test_a_scope_is_required() -> None:
    with pytest.raises(model_mod.InputError, match="scope"):
        model_mod.Request(scope=" ", key="order-8f3a1c2d", body=BODY)


def test_a_body_must_be_a_mapping() -> None:
    with pytest.raises(model_mod.InputError, match="mapping"):
        model_mod.Request(scope="charge", key="order-8f3a1c2d", body=[1])


def test_an_unserialisable_body_is_refused_with_a_reason() -> None:
    with pytest.raises(model_mod.InputError, match="not JSON-serialisable"):
        model_mod.fingerprint_of("charge", {"when": object()})


@pytest.mark.parametrize("status", [0, 99, 600, 1000, -200])
def test_impossible_statuses_are_refused(status: int) -> None:
    with pytest.raises(model_mod.InputError):
        model_mod.Response(status=status, body="{}")


def test_a_boolean_status_is_not_an_integer_status() -> None:
    with pytest.raises(model_mod.InputError, match="integer"):
        model_mod.Response(status=True, body="{}")


def test_a_response_body_must_be_text() -> None:
    with pytest.raises(model_mod.InputError, match="text"):
        model_mod.Response(status=200, body={"ok": True})


def test_the_outcome_line_names_execute_or_replay() -> None:
    executed = model_mod.Outcome("order-8f3a1c2d", 201, "{}", replay=False, attempts=1)
    replayed = model_mod.Outcome("order-8f3a1c2d", 201, "{}", replay=True, attempts=1)
    assert executed.line() == "execute  order-8f3a1c2d       status 201 attempts 1"
    assert replayed.line().startswith("replay  ")


def test_a_mismatch_says_which_two_requests_collided() -> None:
    error = model_mod.Mismatch("order-8f3a1c2d", "aaaa", "bbbb")
    assert "aaaa != bbbb" in str(error)
    assert "one intent" in str(error)
