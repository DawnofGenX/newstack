"""Caesar cipher over small strings.

encode(text, shift) shifts letters, decode reverses, brute_force
tries all twenty-six shifts, and audit stays silent on a valid
round-trip. The promise is checked, never assumed.
"""

from __future__ import annotations

from .solve import (
    ALPHABET,
    MAX_LENGTH,
    CipherError,
    audit,
    brute_force,
    decode,
    encode,
)

__version__ = "0.1.0"

__all__ = [
    "ALPHABET",
    "MAX_LENGTH",
    "CipherError",
    "audit",
    "brute_force",
    "decode",
    "encode",
]
