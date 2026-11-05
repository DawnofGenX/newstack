"""What is allowed, stated once, so the sanitizer has nothing to guess."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from .errors import PolicyError

TAG_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

#: Tags that never have content: emitting a close tag for them is meaningless.
VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

#: Tags whose *content* must go too: dropping only the tag would publish the payload.
DROP_CONTENT = frozenset(
    {
        "script",
        "style",
        "template",
        "iframe",
        "object",
        "embed",
        "noscript",
        "svg",
        "math",
        "frame",
        "frameset",
    }
)

DEFAULT_TAGS = frozenset(
    {
        "a",
        "abbr",
        "b",
        "blockquote",
        "br",
        "code",
        "del",
        "div",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "ins",
        "li",
        "ol",
        "p",
        "pre",
        "q",
        "s",
        "small",
        "span",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "u",
        "ul",
    }
)

DEFAULT_ATTRIBUTES: Mapping[str, frozenset[str]] = {
    "a": frozenset({"href", "title"}),
    "blockquote": frozenset({"cite"}),
    "q": frozenset({"cite"}),
    "td": frozenset({"colspan", "rowspan"}),
    "th": frozenset({"colspan", "rowspan", "scope"}),
}

DEFAULT_SCHEMES = frozenset({"http", "https", "mailto", "tel"})


@dataclass(frozen=True)
class Policy:
    """An allowlist. Anything not named here does not survive."""

    allowed_tags: frozenset[str] = DEFAULT_TAGS
    allowed_attributes: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: dict(DEFAULT_ATTRIBUTES)
    )
    allowed_schemes: frozenset[str] = DEFAULT_SCHEMES
    allow_comments: bool = False

    def __post_init__(self) -> None:
        for tag in self.allowed_tags:
            if not TAG_NAME.match(tag):
                raise PolicyError(f"{tag!r} is not a tag name")
            if tag in DROP_CONTENT:
                reason = f"{tag!r} drops its content; allowing it is a contradiction"
                raise PolicyError(reason)
        for tag, names in self.allowed_attributes.items():
            if tag not in self.allowed_tags:
                raise PolicyError(f"attributes are allowed on {tag!r}, which is not an allowed tag")
            for name in names:
                if not TAG_NAME.match(name):
                    raise PolicyError(f"{name!r} is not an attribute name")
        for scheme in self.allowed_schemes:
            if not TAG_NAME.match(scheme):
                raise PolicyError(f"{scheme!r} is not a scheme")

    def attributes_for(self, tag: str) -> frozenset[str]:
        return frozenset(self.allowed_attributes.get(tag, ()))


DEFAULT = Policy()
