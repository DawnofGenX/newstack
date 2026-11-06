"""The rules this package claims, checked one at a time."""

from __future__ import annotations

import contextlib
import io

from . import cli
from .canonical import CanonicalError, canonical_path, decode, encode, parse_query, request_line
from .sign import Signature, SignatureError, Verifier, sign, signing_string

NOW = 1_780_000_000
SECRET = "selftest-secret"
_state = {"passed": 0, "failed": []}


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        _state["passed"] += 1
    else:
        _state["failed"].append(f"{name}{': ' + detail if detail else ''}")


def refuses(name: str, function, kind: type[Exception], needle: str = "") -> None:
    try:
        function()
    except kind as error:
        if needle and needle not in str(error):
            _state["failed"].append(
                f"{name}: message was {str(error)!r}, wanted {needle!r}"
            )
        else:
            _state["passed"] += 1
        return
    except Exception as error:
        _state["failed"].append(
            f"{name}: raised {type(error).__name__} instead of {kind.__name__}"
        )
        return
    _state["failed"].append(f"{name}: nothing was raised")


def _quiet() -> io.StringIO:
    return io.StringIO()


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = _quiet(), _quiet()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


def _canonical_checks() -> None:
    check("encode keeps unreserved characters", encode("aZ0-_.~") == "aZ0-_.~")
    check("encode capitalises hex", encode(" ") == "%20")
    check("encode handles utf-8", encode("ç") == "%C3%A7")
    check("decode undoes encode", decode(encode("a b/ç")) == "a b/ç")
    check("decode leaves a plus alone", decode("a+b") == "a+b")
    check("decode reads %2B as a plus", decode("%2B") == "+")
    refuses("a broken escape is refused", lambda: decode("%zz"), CanonicalError, "percent escape")
    refuses("a short escape is refused", lambda: decode("%4"), CanonicalError, "percent escape")
    check("a percent path canonicalises", canonical_path("/files/%7Euser") == "/files/~user")
    check("a plain path stays", canonical_path("/files/~user") == "/files/~user")
    refuses(
        "a scheme is refused",
        lambda: request_line("GET", "https://example.test/a"),
        CanonicalError,
        "sign the path",
    )
    refuses("a relative path is refused", lambda: request_line("GET", "a/b"), CanonicalError)
    refuses(
        "a fragment is refused",
        lambda: request_line("GET", "/a#b"),
        CanonicalError,
        "fragment",
    )
    check(
        "an escaped slash stays data",
        request_line("GET", "/a%2Fb")[1] == "/a%2Fb",
    )
    check("the method is uppercased", request_line("post", "/a")[0] == "POST")
    refuses("a non-letter method is refused", lambda: request_line("G3T", "/a"), CanonicalError)
    check(
        "the query is sorted",
        request_line("GET", "/a?b=2&a=1")[1] == "/a?a=1&b=2",
    )
    check("duplicate names are kept", request_line("GET", "/a?k=2&k=1")[1] == "/a?k=1&k=2")
    check("an empty query field is skipped", parse_query("a=1&&b=2") == [("a", "1"), ("b", "2")])
    check("an empty value survives", parse_query("a=") == [("a", "")])
    check("no query means no question mark", request_line("GET", "/a?")[1] == "/a")


def _sign_checks() -> None:
    signature = sign(SECRET, "GET", "/a?b=2&a=1", timestamp=NOW)
    check("a signature is hex of 64", len(signature.value) == 64
          and all(character in "0123456789abcdef" for character in signature.value))
    check("the lifetime is the ttl", signature.expires - signature.timestamp == 300)
    check("lines name the algorithm", signature.lines()[0] == "algorithm    hmac-sha256")
    check("the canonical form is stored", "/a?a=1&b=2" in signature.canonical)
    refuses("a zero lifetime is refused", lambda: sign(SECRET, "GET", "/a", timestamp=NOW,
                                                       ttl_s=0), SignatureError, "positive")
    refuses(
        "a missing signed header is refused",
        lambda: signing_string("GET", "/a", timestamp=NOW, signed_headers=("x-user",)),
        SignatureError,
        "listed as signed",
    )
    text = signing_string("GET", "/a", timestamp=NOW, headers={"X-User": "  a   b  "},
                          signed_headers=("x-user",))
    check("a header line is added", "x-user:a b" in text)
    check("the signing string has six lines", len(text.split("\n")) == 6)
    check("the body hash is covered", "e3b0c442" in signing_string(
        "POST", "/a", timestamp=NOW))
    check("a body changes the string", signing_string("POST", "/a", timestamp=NOW, body=b"x")
          != signing_string("POST", "/a", timestamp=NOW))
    check("two spellings sign identically",
          sign(SECRET, "GET", "/f/%7Euser", timestamp=NOW).value
          == sign(SECRET, "GET", "/f/~user", timestamp=NOW).value)
    check("a reordered query signs identically",
          sign(SECRET, "GET", "/a?b=2&a=1", timestamp=NOW).value
          == sign(SECRET, "GET", "/a?a=1&b=2", timestamp=NOW).value)
    check("a different secret is a different signature",
          sign(SECRET, "GET", "/a", timestamp=NOW).value
          != sign("other", "GET", "/a", timestamp=NOW).value)
    round_trip = Signature.from_dict(signature.as_dict())
    check("as_dict round-trips", round_trip.value == signature.value
          and round_trip.expires == signature.expires)
    refuses("from_dict refuses a non-signature", lambda: Signature.from_dict({"timestamp": 1}),
            SignatureError, "not a signature")


def _verifier_checks() -> None:
    signature = sign(SECRET, "POST", "/orders", timestamp=NOW, body=b"x")
    verdict = Verifier(SECRET).verify("POST", "/orders", signature, now_s=NOW, body=b"x")
    check("a fresh signature is accepted", verdict.ok and verdict.line().startswith("ok"))
    check("the verdict names the life left", "300 s of life left" in verdict.reason)
    check("a different body is refused",
          not Verifier(SECRET).verify("POST", "/orders", signature, now_s=NOW, body=b"y").ok)
    check("a different path is refused",
          not Verifier(SECRET).verify("POST", "/other", signature, now_s=NOW, body=b"x").ok)
    check("a different method is refused",
          not Verifier(SECRET).verify("PUT", "/orders", signature, now_s=NOW, body=b"x").ok)
    check("a different secret is refused",
          not Verifier("other").verify("POST", "/orders", signature, now_s=NOW, body=b"x").ok)
    check("the mismatch reason is honest",
          Verifier("other").verify("POST", "/orders", signature, now_s=NOW,
                                   body=b"x").reason == "the signature does not match this request")
    check("on the expiry second it is still valid",
          Verifier(SECRET).verify("POST", "/orders", signature,
                                  now_s=signature.expires, body=b"x").ok)
    late = Verifier(SECRET).verify("POST", "/orders", signature, now_s=signature.expires + 5,
                                   body=b"x")
    check("one second late it is refused", not late.ok and late.reason == "expired 5 s ago")
    future = Verifier(SECRET).verify("POST", "/orders", signature, now_s=NOW - 120, body=b"x")
    check("a future timestamp is refused", not future.ok and "future" in future.reason)
    near_future = Verifier(SECRET).verify("POST", "/orders", signature, now_s=NOW - 30, body=b"x")
    check("a small skew is tolerated", near_future.ok)
    replay = Verifier(SECRET)
    first = replay.verify("POST", "/orders", signature, now_s=NOW, body=b"x")
    second = replay.verify("POST", "/orders", signature, now_s=NOW + 1, body=b"x")
    check("a replay is refused", first.ok and not second.ok)
    check("the replay reason names the earlier use",
          "already accepted" in second.reason and f"at {NOW}" in second.reason)
    check("forget_expired drops a dead nonce", replay.forget_expired(NOW + 400) == 1)
    check("a forgotten nonce stays refused",
          "expired" in replay.verify("POST", "/orders", signature, now_s=NOW + 401).reason)
    bad_algorithm = Signature(value="0" * 64, timestamp=NOW, expires=NOW + 300,
                              signed_headers=(), canonical="", algorithm="md5")
    check("an unknown algorithm is refused",
          "not hmac-sha256" in Verifier(SECRET).verify("POST", "/orders", bad_algorithm,
                                                       now_s=NOW).reason)
    refuses("a zero verifier lifetime is refused", lambda: Verifier(SECRET, ttl_s=0),
            SignatureError, "positive")
    refuses("a negative skew is refused", lambda: Verifier(SECRET, skew_s=-1),
            SignatureError, "negative")


def _cli_checks() -> None:
    code, out, _ = _run(["sign", "--url", "/a?b=2&a=1", "--secret", SECRET,
                         "--timestamp", str(NOW)])
    check("sign exits 0", code == 0)
    check("sign prints the algorithm", "algorithm    hmac-sha256" in out)
    check("sign prints the canonical target", "/a?a=1&b=2" in out)
    code, out, _ = _run(["sign", "--url", "/a", "--secret", SECRET, "--timestamp", str(NOW),
                         "--show-string"])
    check("--show-string prints the covered text", "signing string" in out and "hmac-sha256" in out)
    code, out, _ = _run(["string", "--url", "/a", "--timestamp", str(NOW)])
    check("string exits 0", code == 0)
    check("string prints five lines",
          len([line for line in out.splitlines() if line]) == 5)
    code, out, _ = _run(["sign", "--url", "/a", "--secret", SECRET,
                         "--timestamp", str(NOW), "--json"])
    check("--json prints an object", out.strip().startswith("{") and '"signature"' in out)
    code, _, err = _run(["sign", "--url", "https://example.test/a", "--secret", SECRET,
                         "--timestamp", str(NOW)])
    check("a host is exit 2", code == 2)
    check("the host refusal is explained", "sign the path" in err)
    code, _, err = _run(["sign", "--url", "/a", "--secret", SECRET, "--header", "broken"])
    check("a malformed header is exit 2", code == 2 and "name:value" in err)
    code, _, err = _run(["verify", "--url", "/a", "--secret", SECRET, "--now", str(NOW)])
    check("verify without a signature is exit 2", code == 2 and "--signature" in err)
    signature = sign(SECRET, "GET", "/a", timestamp=NOW)
    code, out, _ = _run(["verify", "--url", "/a", "--secret", SECRET, "--now", str(NOW),
                         "--signature", signature.value, "--timestamp", str(NOW),
                         "--expires", str(signature.expires)])
    check("a good signature is exit 0", code == 0 and out.startswith("ok"))
    code, out, _ = _run(["verify", "--url", "/b", "--secret", SECRET, "--now", str(NOW),
                         "--signature", signature.value, "--timestamp", str(NOW),
                         "--expires", str(signature.expires)])
    check("a tampered url is exit 1", code == 1 and out.startswith("refused"))
    code, out, _ = _run(["demo"])
    check("the demo exits 0", code == 0)
    check("six stories are printed", out.count("-> holds") == 6)
    code, _, err = _run(["sign", "--url", "/a", "--secret", SECRET, "--ttl", "0",
                         "--timestamp", str(NOW)])
    check("a zero ttl is exit 2", code == 2 and "positive" in err)


def main() -> int:
    for part in (_canonical_checks, _sign_checks, _verifier_checks, _cli_checks):
        part()
    if _state["failed"]:
        print(f"selftest: {len(_state['failed'])} check(s) failed")
        for failure in _state["failed"]:
            print(f"  {failure}")
        return 1
    print(f"selftest: {_state['passed']} checks passed")
    return 0
