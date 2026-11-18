"""Offline self-test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from cryptography.fernet import InvalidToken

from .vault import decrypt_file, encrypt_file


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        vault = base / "vault"
        plain = base / "plain.txt"
        plain.write_text("hello vault", encoding="utf-8")
        entry_id = encrypt_file(vault, plain, "correct")
        out = base / "out.txt"
        decrypt_file(vault, entry_id, "correct", out)
        assert out.read_text(encoding="utf-8") == "hello vault"
        try:
            decrypt_file(vault, entry_id, "wrong", base / "bad.txt")
        except InvalidToken:
            pass
        else:
            raise AssertionError("wrong password did not fail")
        cipher = vault / f"{entry_id}.bin"
        data = bytearray(cipher.read_bytes())
        data[0] ^= 1
        cipher.write_bytes(data)
        try:
            decrypt_file(vault, entry_id, "correct", base / "tampered.txt")
        except InvalidToken:
            pass
        else:
            raise AssertionError("tampering not detected")
    print("selftest: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
