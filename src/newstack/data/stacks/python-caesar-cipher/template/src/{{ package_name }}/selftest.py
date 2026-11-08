"""The promises this cipher makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    ALPHABET,
    MAX_LENGTH,
    CipherError,
    audit,
    brute_force,
    decode,
    encode,
)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    _lines: list = field(default_factory=list)

    def section(self, title: str) -> None:
        self._lines.append(f"## {title}")

    def equal(self, name: str, got, want) -> None:
        self.checks += 1
        if got == want:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}: {got!r} != {want!r}")

    def ok(self, name: str, cond: bool) -> None:
        self.checks += 1
        if cond:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}")

    def refuses(self, name: str, fn, exc) -> None:
        self.checks += 1
        try:
            fn()
        except exc:
            self._lines.append(f"ok   {name}")
            return
        except Exception as other:
            self.failed += 1
            self._lines.append(f"FAIL {name}: raised {type(other).__name__}")
            return
        self.failed += 1
        self._lines.append(f"FAIL {name}: did not raise")

    def render(self) -> str:
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self._lines, "", tail))


FIXTURE = "each letter is shifted by the same amount, round-trips recover the text"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("encode abc shift 3", encode("abc", 3), "def")
    report.equal("decode def shift 3", decode("def", 3), "abc")
    report.equal("shift zero identity", encode("abc", 0), "abc")
    report.equal("wrap around", encode("xyz", 3), "abc")
    report.equal("non-letters stay", encode("a b!", 3), "d e!")


def _roundtrip(report: Report) -> None:
    report.section("round-trip")
    for text in ("", "abc", "Hello, World!", "xyzXYZ"):
        report.ok(f"round-trip {text!r}", decode(encode(text, 7), 7) == text)
    report.equal("audit valid", audit("abc", 3), [])


def _brute(report: Report) -> None:
    report.section("brute force")
    report.equal("26 shifts", len(brute_force("abc")), ALPHABET)
    report.ok("one shift recovers", any(t == "abc" for _, t in brute_force(encode("abc", 5))))


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("too long", lambda: encode("a" * (MAX_LENGTH + 1), 1), CipherError)
    report.refuses("non-str", lambda: encode(123, 1), CipherError)
    report.refuses("non-int shift", lambda: encode("abc", "a"), CipherError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(7)
    for _ in range(30):
        n = rng.randint(0, 12)
        text = "".join(rng.choice("abcXYZ !") for _ in range(n))
        shift = rng.randint(0, 25)
        try:
            enc = encode(text, shift)
        except CipherError:
            continue
        report.ok("round-trip holds", decode(enc, shift) == text)
        report.ok("audit silent", audit(text, shift) == [])


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the cipher module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _roundtrip(report)
    _brute(report)
    _refusal(report)
    _oracle(report)
    _stories(report)
    return report
