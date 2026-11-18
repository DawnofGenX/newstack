from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken

from {{ package_name }}.vault import decrypt_file, encrypt_file, list_entries


def test_round_trip(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    source = tmp_path / "secret.txt"
    source.write_text("top secret", encoding="utf-8")
    entry_id = encrypt_file(vault, source, "pw")
    out = tmp_path / "out.txt"
    decrypt_file(vault, entry_id, "pw", out)
    assert out.read_text(encoding="utf-8") == "top secret"
    entries = list_entries(vault)
    assert len(entries) == 1
    assert entries[0]["id"] == entry_id


def test_wrong_password(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    source = tmp_path / "secret.txt"
    source.write_text("top secret", encoding="utf-8")
    entry_id = encrypt_file(vault, source, "pw")
    with pytest.raises(InvalidToken):
        decrypt_file(vault, entry_id, "wrong", tmp_path / "out.txt")


def test_tamper_detection(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    source = tmp_path / "secret.txt"
    source.write_text("top secret", encoding="utf-8")
    entry_id = encrypt_file(vault, source, "pw")
    cipher = vault / f"{entry_id}.bin"
    data = bytearray(cipher.read_bytes())
    data[-1] ^= 1
    cipher.write_bytes(data)
    with pytest.raises(InvalidToken):
        decrypt_file(vault, entry_id, "pw", tmp_path / "out.txt")
