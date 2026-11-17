"""Content-addressed store."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

MANIFEST_NAME = "manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Store:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / MANIFEST_NAME
        self._manifest: dict[str, str] = {}
        if self.manifest_path.exists():
            self._manifest = json.loads(self.manifest_path.read_text())

    def _blob_path(self, digest: str) -> Path:
        return self.root / digest[:2] / digest

    def _atomic_write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def _save_manifest(self) -> None:
        data = json.dumps(self._manifest, indent=2, sort_keys=True).encode()
        self._atomic_write(self.manifest_path, data)

    def put(self, data: bytes, name: str | None = None) -> str:
        digest = sha256_bytes(data)
        blob = self._blob_path(digest)
        if not blob.exists():
            self._atomic_write(blob, data)
        if name is not None:
            self._manifest[name] = digest
            self._save_manifest()
        return digest

    def put_file(self, src: str | Path, name: str | None = None) -> str:
        data = Path(src).read_bytes()
        return self.put(data, name=name if name is not None else Path(src).name)

    def get(self, name: str) -> bytes:
        digest = self._manifest[name]
        return self._blob_path(digest).read_bytes()

    def has(self, name: str) -> bool:
        return name in self._manifest

    def delete(self, name: str) -> None:
        self._manifest.pop(name, None)
        self._save_manifest()

    def referenced_digests(self) -> set[str]:
        return set(self._manifest.values())

    def verify(self) -> dict[str, Any]:
        errors: list[str] = []
        for name, digest in self._manifest.items():
            blob = self._blob_path(digest)
            if not blob.exists():
                errors.append(f"missing blob for {name}: {digest}")
                continue
            data = blob.read_bytes()
            if sha256_bytes(data) != digest:
                errors.append(f"hash mismatch for {name}: {digest}")
        # orphan check not an error in verify? report
        return {"ok": not errors, "errors": errors, "entries": len(self._manifest)}

    def gc(self) -> int:
        referenced = self.referenced_digests()
        freed = 0
        for d in self.root.rglob("*"):
            if d.is_file() and d.name != MANIFEST_NAME and len(d.name) == 64 and d.name not in referenced:
                size = d.stat().st_size
                d.unlink()
                freed += size
        # remove empty shard dirs
        for d in sorted(self.root.iterdir(), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        return freed

    def blob_count(self) -> int:
        n = 0
        for d in self.root.rglob("*"):
            if d.is_file() and d.name != MANIFEST_NAME and len(d.name) == 64:
                n += 1
        return n

    def total_bytes(self) -> int:
        total = 0
        for d in self.root.rglob("*"):
            if d.is_file() and d.name != MANIFEST_NAME and len(d.name) == 64:
                total += d.stat().st_size
        return total