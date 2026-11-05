"""Application protocol: JSON text frames -> JSON text replies."""

import json

WORD_SEPARATORS = " \t\n\r\v\f"
MAX_MESSAGE_BYTES = 64 * 1024  # 65536 passes, 65537 closes 1009


def _error(name: str) -> str:
    return json.dumps({"type": "error", "error": name})


def count_stats(text: str) -> dict:
    """lines/words/bytes per the wire contract.

    bytes = raw UTF-8 length; words split on exactly space \\t \\n \\r \\v \\f
    (NOT str.split(), which also splits on \\x1c-\\x1f and \\x85).
    """
    raw = text.encode("utf-8")
    lines = len(text.splitlines())
    words = 0
    in_word = False
    for ch in text:
        if ch in WORD_SEPARATORS:
            in_word = False
        else:
            if not in_word:
                words += 1
            in_word = True
    return {"lines": lines, "words": words, "bytes": len(raw)}


def dispatch(raw: bytes):
    """Handle one text message. Returns reply text, or None for no reply."""
    try:
        msg = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return _error("invalid_json")
    if not isinstance(msg, dict):
        return _error("unknown_type")
    mtype = msg.get("type")
    if mtype == "ping":
        return json.dumps({"type": "pong"})
    if mtype in ("stats", "echo"):
        text = msg.get("text")
        if not isinstance(text, str):
            return _error("invalid_text")
        if mtype == "echo":
            return json.dumps({"type": "echo", "text": text})
        return json.dumps({"type": "stats", **count_stats(text)})
    return _error("unknown_type")
