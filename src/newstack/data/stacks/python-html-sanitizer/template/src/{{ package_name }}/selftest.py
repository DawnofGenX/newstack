"""The same claims the demo makes, without the prose, in one process."""

from __future__ import annotations

import sys

from . import demo
from .audit import audit, problems
from .errors import PolicyError, SanitizeError
from .policy import DEFAULT, Policy
from .sanitize import explain, sanitize, scheme_of, url_is_allowed


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, description: str, condition: bool) -> None:
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            print(f"FAIL  {description}", file=sys.stderr)

    def equal(self, description: str, want: object, got: object) -> None:
        self.ok(
            f"{description} (wanted {want!r}, got {got!r})" if want != got else description,
            want == got,
        )

    def raises(self, description: str, function, *args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except (PolicyError, SanitizeError, ValueError):
            self.passed += 1
            return
        self.failed += 1
        print(f"FAIL  {description} (nothing was raised)", file=sys.stderr)


def _policy_checks(checks: Checks) -> None:
    checks.equal("a paragraph is allowed", True, "p" in DEFAULT.allowed_tags)
    checks.equal("a script is not", False, "script" in DEFAULT.allowed_tags)
    checks.equal(
        "an anchor may carry href", frozenset({"href", "title"}), DEFAULT.attributes_for("a")
    )
    checks.equal("a paragraph may carry nothing", frozenset(), DEFAULT.attributes_for("p"))
    checks.raises(
        "a policy cannot name attributes on a tag it does not allow",
        Policy,
        frozenset({"p"}),
        {"a": frozenset({"href"})},
    )
    checks.raises("a content-dropping tag cannot be allowed", Policy, frozenset({"script"}))
    checks.raises(
        "a policy cannot name a fake scheme",
        Policy,
        DEFAULT.allowed_tags,
        {},
        frozenset({"java script"}),
    )
    permissive = Policy(DEFAULT.allowed_tags | {"img"}, {"img": frozenset({"alt"})})
    checks.equal(
        "a custom policy can allow what the default does not",
        frozenset({"alt"}),
        permissive.attributes_for("img"),
    )


def _scheme_checks(checks: Checks) -> None:
    checks.equal("a plain url has its scheme", "javascript", scheme_of("javascript:alert(1)"))
    checks.equal(
        "a tab inside the scheme is ignored", "javascript", scheme_of("jav\tascript:alert(1)")
    )
    checks.equal(
        "a newline inside the scheme is ignored", "javascript", scheme_of("java\nscript:alert(1)")
    )
    checks.equal("a relative path has no scheme", None, scheme_of("/docs/page"))
    checks.equal("a fragment has no scheme", None, scheme_of("#top"))
    checks.equal("a slash inside the head means relative", None, scheme_of("a/b:c"))
    checks.equal(
        "the scheme is compared case-insensitively", "http", scheme_of("HTTP://example.com")
    )
    checks.equal("mailto is a scheme", "mailto", scheme_of("mailto:someone@example.com"))
    checks.equal("https is allowed", True, url_is_allowed("https://example.com/a?b=1"))
    checks.equal("javascript is not", False, url_is_allowed("javascript:alert(1)"))
    checks.equal("data is not", False, url_is_allowed("data:text/html,<script>alert(1)</script>"))
    checks.equal("a relative url is allowed", True, url_is_allowed("/safe"))


def _output_checks(checks: Checks) -> None:
    for name, source, _note in demo.VECTORS:
        verdict = audit(source)
        checks.ok(f"the vector holds: {name}", verdict.ok)
    checks.equal("text is escaped, not dropped", "a &lt; b &amp; c", sanitize("a < b & c"))
    checks.equal(
        "attribute quotes are escaped",
        '<a title="a&quot;b">x</a>',
        sanitize('<a title="a&quot;b">x</a>'),
    )
    checks.equal(
        "attributes are emitted in one order",
        '<a href="/x" title="y">z</a>',
        sanitize('<a title="y" href="/x">z</a>'),
    )
    checks.equal("an unclosed element is closed", "<b>x</b>", sanitize("<b>x"))
    checks.equal("a void element is not closed", "a<br>b", sanitize("a<br>b"))
    checks.equal(
        "a self-closed anchor is written out", '<a href="/x"></a>', sanitize('<a href="/x" />')
    )
    checks.equal("a close tag with no open tag is dropped", "x", sanitize("x</b>"))
    checks.equal("a doctype is not content", "<p>x</p>", sanitize("<!doctype html><p>x</p>"))
    checks.equal(
        "nested same-name tags close in order", "<b><b>x</b></b>", sanitize("<b><b>x</b></b>")
    )
    checks.equal(
        "an allowed tag with a bad url keeps the element",
        "<a>t</a>",
        sanitize('<a href="javascript:1">t</a>'),
    )
    checks.equal(
        "an allowed tag with a good url keeps both",
        '<a href="tel:x">t</a>',
        sanitize('<a href="tel:x">t</a>'),
    )
    _output, stats = explain('<img src=x onclick="a"><b>t</b>')
    checks.equal("the counters name what was removed", 1, stats.tags_dropped)
    checks.equal("an attribute with no value is dropped", "<p>t</p>", sanitize("<p hidden>t</p>"))
    comments = Policy(allow_comments=True)
    checks.equal(
        "a policy can keep comments",
        "<p>t</p><!-- note -->",
        sanitize("<p>t</p><!-- note -->", comments),
    )
    kept = sanitize("<!-- -- note -->", comments)
    body = kept.removeprefix("<!--").removesuffix("-->")
    checks.equal("a comment cannot carry -- through", False, "--" in body)


def _audit_checks(checks: Checks) -> None:
    checks.equal("the scanner sees a script tag", 1, len(problems("<script>alert(1)</script>")))
    checks.equal("the scanner sees an inline handler", 1, len(problems('<p onclick="x">y</p>')))
    checks.equal(
        "the scanner ignores words in text", 0, len(problems("<p>javascript:alert(1)</p>"))
    )
    cleaned = sanitize('<a href="javascript:1">x</a>')
    checks.equal("sanitized output is clean", 0, len(problems(cleaned)))
    verdict = audit("<b>x</b>")
    checks.equal("audit marks a clean input as ok", True, verdict.ok)
    checks.equal("audit reports the output, not the input", "<b>x</b>", verdict.output)
    broken = audit("<script>x</script>")
    checks.equal("audit counts the dropped block", 1, broken.stats.content_dropped)

    steps = demo.run()
    checks.equal("the demo has eight vectors", 8, len(steps))
    checks.equal("every vector holds", 0, sum(1 for step in steps if not step.ok))


def run() -> int:
    checks = Checks()
    for group in (_policy_checks, _scheme_checks, _output_checks, _audit_checks):
        group(checks)
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
