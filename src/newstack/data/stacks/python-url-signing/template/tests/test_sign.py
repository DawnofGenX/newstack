"""Signing and verifying."""

from __future__ import annotations

import pytest

from {{ package_name }} import sign as subject

SECRET = "test-secret"
NOW = 1_780_000_000


def test_a_signature_is_sixty_four_hex_characters() -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW)
    assert len(signature.value) == 64
    assert int(signature.value, 16) >= 0


def test_the_expiry_is_the_timestamp_plus_the_lifetime() -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW, ttl_s=90)
    assert signature.expires == NOW + 90


def test_a_zero_lifetime_is_refused() -> None:
    with pytest.raises(subject.SignatureError, match="positive"):
        subject.sign(SECRET, "GET", "/a", timestamp=NOW, ttl_s=0)


def test_a_signed_header_that_is_absent_is_refused() -> None:
    with pytest.raises(subject.SignatureError, match="listed as signed"):
        subject.signing_string("GET", "/a", timestamp=NOW, signed_headers=("x-user",))


def test_header_whitespace_is_collapsed() -> None:
    text = subject.signing_string(
        "GET", "/a", timestamp=NOW, headers={"X-User": " a   b "}, signed_headers=("x-user",)
    )
    assert "x-user:a b" in text


def test_the_body_is_part_of_the_signing_string() -> None:
    empty = subject.signing_string("POST", "/a", timestamp=NOW)
    body = subject.signing_string("POST", "/a", timestamp=NOW, body=b"{}")
    assert empty != body


def test_reordered_queries_sign_identically() -> None:
    left = subject.sign(SECRET, "GET", "/a?b=2&a=1", timestamp=NOW)
    right = subject.sign(SECRET, "GET", "/a?a=1&b=2", timestamp=NOW)
    assert left.value == right.value


def test_a_verifier_accepts_a_fresh_signature() -> None:
    signature = subject.sign(SECRET, "POST", "/orders", timestamp=NOW, body=b"x")
    verdict = subject.Verifier(SECRET).verify("POST", "/orders", signature, now_s=NOW, body=b"x")
    assert verdict.ok
    assert verdict.line().startswith("ok")


def test_a_changed_body_is_refused() -> None:
    signature = subject.sign(SECRET, "POST", "/orders", timestamp=NOW, body=b"x")
    verdict = subject.Verifier(SECRET).verify(
        "POST", "/orders", signature, now_s=NOW, body=b"y"
    )
    assert verdict.reason == "the signature does not match this request"


def test_the_expiry_second_still_passes_and_the_next_one_does_not() -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW, ttl_s=10)
    assert subject.Verifier(SECRET).verify("GET", "/a", signature, now_s=NOW + 10).ok
    late = subject.Verifier(SECRET).verify("GET", "/a", signature, now_s=NOW + 12)
    assert late.reason == "expired 2 s ago"


def test_a_timestamp_far_in_the_future_is_refused() -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW + 600)
    verdict = subject.Verifier(SECRET).verify("GET", "/a", signature, now_s=NOW)
    assert not verdict.ok
    assert "future" in verdict.reason


def test_a_signature_is_a_one_time_token() -> None:
    signature = subject.sign(SECRET, "POST", "/orders", timestamp=NOW)
    verifier = subject.Verifier(SECRET)
    assert verifier.verify("POST", "/orders", signature, now_s=NOW).ok
    second = verifier.verify("POST", "/orders", signature, now_s=NOW)
    assert second.reason == f"this signature was already accepted at {NOW}"


def test_forgetting_a_nonce_leaves_the_expiry_check_in_charge() -> None:
    signature = subject.sign(SECRET, "GET", "/a", timestamp=NOW)
    verifier = subject.Verifier(SECRET)
    verifier.verify("GET", "/a", signature, now_s=NOW)
    assert verifier.forget_expired(NOW + 400) == 1
    assert "expired" in verifier.verify("GET", "/a", signature, now_s=NOW + 401).reason


def test_an_unknown_algorithm_is_refused() -> None:
    signature = subject.Signature(
        value="0" * 64,
        timestamp=NOW,
        expires=NOW + 300,
        signed_headers=(),
        canonical="",
        algorithm="md5",
    )
    verdict = subject.Verifier(SECRET).verify("GET", "/a", signature, now_s=NOW)
    assert "not hmac-sha256" in verdict.reason


def test_a_negative_skew_allowance_is_refused() -> None:
    with pytest.raises(subject.SignatureError, match="negative"):
        subject.Verifier(SECRET, skew_s=-1)
