"""Reading the `text` member out of a request body, with the three outcomes the
contract distinguishes: found, missing, or not JSON at all.

`json.loads` raises one exception type (`JSONDecodeError`) for syntax and another
(`UnicodeDecodeError`) for a body that is not UTF-8, and a body that decodes to
`[1, 2]` or `"a string"` parses fine but has no member to read. Only the first of
those is `invalid_json`; the other two are `missing_text`, which is a different
answer to the client.
"""

from __future__ import annotations

import json
from typing import Literal

Outcome = Literal["found", "missing", "invalid"]


def read_text_member(body: bytes) -> tuple[Outcome, str]:
    """Return `(outcome, text)`; `text` is only meaningful when outcome is `found`."""
    if not body.strip():
        return "missing", ""
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid", ""
    if not isinstance(document, dict):
        return "missing", ""
    value = document.get("text")
    if not isinstance(value, str):
        return "missing", ""
    return "found", value
