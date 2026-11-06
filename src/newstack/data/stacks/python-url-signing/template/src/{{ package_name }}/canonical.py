"""One spelling for a request, so a signature can survive a copy.

Two clients can send the same request with different bytes: `%7e` and `~` are
the same character, query parameters can be reordered, and a form encoder
writes a space as `+`. A signature over the raw URL breaks on every one of
those. A signature over a canonical form survives them, and that is the only
difference between an API that works and one that fails intermittently. The
canonical form is the contract; the raw URL is only one spelling of it.
"""

from __future__ import annotations

UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
)
HEX = "0123456789abcdefABCDEF"


class CanonicalError(ValueError):
    """The request cannot be put into canonical form."""


def encode(text: str) -> str:
    """Percent-encode everything that is not unreserved, in uppercase hex."""
    out: list[str] = []
    for byte in text.encode("utf-8"):
        character = chr(byte)
        if character in UNRESERVED:
            out.append(character)
        else:
            out.append(f"%{byte:02X}")
    return "".join(out)


def _byte_at(text: str, index: int) -> int:
    following = text[index + 1 : index + 3]
    if len(following) != 2 or not all(character in HEX for character in following):
        raise CanonicalError(
            f"'{text[index:index + 3]}' is not a percent escape: a percent sign must be "
            "followed by two hexadecimal digits, so this text cannot be decoded"
        )
    return int(following, 16)


def decode(text: str) -> str:
    """Undo percent-encoding. A plus sign is a plus sign, not a space."""
    out = bytearray()
    index = 0
    while index < len(text):
        character = text[index]
        if character == "%":
            out.append(_byte_at(text, index))
            index += 3
        else:
            out.extend(character.encode("utf-8"))
            index += 1
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CanonicalError(f"the escapes are not valid UTF-8: {error}") from error


def split_url(url: str) -> tuple[str, str]:
    """Return (path, raw query) and refuse anything that is not an absolute path."""
    if "://" in url:
        raise CanonicalError(
            f"'{url}' carries a scheme and a host: sign the path, because the host is how "
            "the request was routed, not what it asks for"
        )
    if not url.startswith("/"):
        raise CanonicalError(f"'{url}' is not an absolute path: it must start with '/'")
    path, _, query = url.partition("?")
    if "#" in query or "#" in path:
        raise CanonicalError("a fragment is never sent to the server, so it cannot be signed")
    return path, query


def canonical_path(path: str) -> str:
    """Decode then re-encode each segment, keeping the slashes between them.

    The split happens on a LITERAL slash, so an escaped `%2F` stays data instead
    of becoming another separator: `/a%2Fb` is one segment named `a/b`, and
    rewriting it as `/a/b` would change which resource the request names.
    """
    return "/".join(encode(decode(segment)) for segment in path.split("/"))


def parse_query(query: str) -> list[tuple[str, str]]:
    """Decoded (name, value) pairs, duplicates kept."""
    if not query:
        return []
    pairs = []
    for field in query.split("&"):
        if not field:
            continue
        name, _, value = field.partition("=")
        pairs.append((decode(name), decode(value)))
    return pairs


def canonical_query(pairs: list[tuple[str, str]]) -> str:
    """Sort by encoded name then encoded value; encode both."""
    rendered = sorted((encode(name), encode(value)) for name, value in pairs)
    return "&".join(f"{name}={value}" for name, value in rendered)


def request_line(method: str, url: str) -> tuple[str, str]:
    """The method and the canonical path-plus-query for one request."""
    upper = method.upper()
    if not upper.isalpha():
        raise CanonicalError(f"'{method}' is not a method: methods are letters")
    path, query = split_url(url)
    text = canonical_path(path)
    rendered = canonical_query(parse_query(query))
    if rendered:
        text = f"{text}?{rendered}"
    return upper, text
