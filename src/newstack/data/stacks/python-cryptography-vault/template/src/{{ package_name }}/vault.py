from __future__ import annotations

import base64
import json
import os
import uuid
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 390000


def _vault(vault: Path) -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    return vault


def _manifest_path(vault: Path) -> Path:
    return vault / "manifest.json"


def _load_manifest(vault: Path) -> dict:
    path = _manifest_path(vault)
    if not path.exists():
        return {"entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_manifest(vault: Path, manifest: dict) -> None:
    _manifest_path(vault).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_file(vault: Path | str, source: Path | str, password: str) -> str:
    vault = _vault(Path(vault))
    source = Path(source)
    salt = os.urandom(16)
    key = derive_key(password, salt)
    token = Fernet(key).encrypt(source.read_bytes())
    entry_id = uuid.uuid4().hex
    (vault / f"{entry_id}.bin").write_bytes(token)
    manifest = _load_manifest(vault)
    manifest["entries"].append(
        {
            "id": entry_id,
            "name": source.name,
            "salt": base64.b64encode(salt).decode("ascii"),
            "ciphertext": f"{entry_id}.bin",
        }
    )
    _save_manifest(vault, manifest)
    return entry_id


def _find_entry(vault: Path, entry_id: str) -> dict:
    manifest = _load_manifest(vault)
    for entry in manifest["entries"]:
        if entry["id"] == entry_id:
            return entry
    raise KeyError(f"unknown entry: {entry_id}")


def decrypt_file(vault: Path | str, entry_id: str, password: str, destination: Path | str | None = None) -> Path:
    vault = Path(vault)
    entry = _find_entry(vault, entry_id)
    salt = base64.b64decode(entry["salt"])
    key = derive_key(password, salt)
    token = (vault / entry["ciphertext"]).read_bytes()
    data = Fernet(key).decrypt(token)
    if destination is None:
        destination = Path(entry["name"])
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return destination


def list_entries(vault: Path | str) -> list[dict]:
    vault = Path(vault)
    if not vault.exists():
        return []
    return _load_manifest(vault)["entries"]
