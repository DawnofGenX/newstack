"""Rebuild markup from an allowlist: nothing from the input is copied through.

The input is never edited, filtered or patched. It is parsed into events, and
the output is *written* from those events, so a construct the parser did not
understand cannot survive as text that a browser will understand later.
"""

from __future__ import annotations

import html as html_module
from dataclasses import dataclass
from html.parser import HTMLParser

from .errors import SanitizeError
from .policy import DEFAULT, DROP_CONTENT, TAG_NAME, VOID_TAGS, Policy


@dataclass
class Stats:
    """What the policy removed. Reported, because a silent removal is a bug."""

    tags_dropped: int = 0
    attributes_dropped: int = 0
    urls_refused: int = 0
    content_dropped: int = 0
    comments_dropped: int = 0
    characters_dropped: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "tags_dropped": self.tags_dropped,
            "attributes_dropped": self.attributes_dropped,
            "urls_refused": self.urls_refused,
            "content_dropped": self.content_dropped,
            "comments_dropped": self.comments_dropped,
            "characters_dropped": self.characters_dropped,
        }

    def line(self) -> str:
        return (
            f"dropped  {self.tags_dropped} tag(s), {self.attributes_dropped} attribute(s), "
            f"{self.urls_refused} url(s) refused, {self.content_dropped} content block(s)"
        )


def scheme_of(url: str) -> str | None:
    """The scheme a browser would see, ignoring what it ignores.

    Browsers drop ASCII whitespace and control characters *inside* a scheme, so
    `java\tscript:` is `javascript:` to them. Anything here that is not a plain
    scheme name is a relative reference, which has no scheme at all.
    """
    cleaned = "".join(ch for ch in url if ch.isprintable() and not ch.isspace() and ord(ch) >= 32)
    head, separator, _rest = cleaned.partition(":")
    if not separator:
        return None
    candidate = head.lower()
    if not TAG_NAME.match(candidate):
        return None
    return candidate


def url_is_allowed(url: str, policy: Policy = DEFAULT) -> bool:
    scheme = scheme_of(url)
    return scheme is None or scheme in policy.allowed_schemes


class Sanitizer(HTMLParser):
    """A parser that writes: the output is composed from allowed events only."""

    def __init__(self, policy: Policy = DEFAULT) -> None:
        super().__init__(convert_charrefs=True)
        self.policy = policy
        self.stats = Stats()
        self._out: list[str] = []
        self._open: list[str] = []
        self._skipping: list[str] = []

    # -- events ---------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        if self._skipping:
            if name == self._skipping[-1]:
                self._skipping.append(name)
            return
        if name in self.policy.allowed_tags:
            self._out.append(self._render(name, self._filter(name, attrs)))
            if name not in VOID_TAGS:
                self._open.append(name)
            return
        if name in DROP_CONTENT:
            self._skipping.append(name)
            self.stats.content_dropped += 1
            return
        self.stats.tags_dropped += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if self._skipping:
            if name == self._skipping[-1]:
                self._skipping.pop()
            return
        if name not in self._open:
            return
        index = len(self._open) - 1 - self._open[::-1].index(name)
        for open_tag in reversed(self._open[index:]):
            self._out.append(f"</{open_tag}>")
        del self._open[index:]

    def handle_data(self, data: str) -> None:
        if self._skipping:
            self.stats.characters_dropped += len(data)
            return
        self._out.append(html_module.escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self._out.append(f"&amp;{name};")

    def handle_charref(self, name: str) -> None:
        self._out.append(f"&amp;#{name};")

    def handle_comment(self, data: str) -> None:
        if not self.policy.allow_comments:
            self.stats.comments_dropped += 1
            return
        self._out.append(f"<!--{data.replace('--', '- -')}-->")

    def handle_decl(self, decl: str) -> None:
        self.stats.tags_dropped += 1

    def unknown_decl(self, data: str) -> None:
        self.stats.tags_dropped += 1

    def handle_pi(self, data: str) -> None:
        self.stats.tags_dropped += 1

    # -- building -------------------------------------------------------
    def _filter(self, tag: str, attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        allowed = self.policy.attributes_for(tag)
        kept: dict[str, str] = {}
        for name, value in attrs:
            lowered = name.lower()
            if lowered not in allowed or value is None:
                self.stats.attributes_dropped += 1
                continue
            if lowered in {"href", "cite"} and not url_is_allowed(value, self.policy):
                self.stats.urls_refused += 1
                continue
            kept[lowered] = value
        return kept

    @staticmethod
    def _render(tag: str, attrs: dict[str, str]) -> str:
        parts = [
            f' {name}="{html_module.escape(value, quote=True)}"'
            for name, value in sorted(attrs.items())
        ]
        return f"<{tag}{''.join(parts)}>"

    def result(self) -> str:
        while self._open:
            self._out.append(f"</{self._open.pop()}>")
        return "".join(self._out)


def explain(text: str, policy: Policy = DEFAULT) -> tuple[str, Stats]:
    """Sanitize `text` and return the output with what was removed."""
    if not isinstance(text, str):
        raise SanitizeError(f"expected text, got {type(text).__name__}")
    sanitizer = Sanitizer(policy)
    sanitizer.feed(text)
    sanitizer.close()
    return sanitizer.result(), sanitizer.stats


def sanitize(text: str, policy: Policy = DEFAULT) -> str:
    return explain(text, policy)[0]
