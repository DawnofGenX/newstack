"""Offline self-test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image

from .thumbnailer import thumbnail


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "a.png"
        Image.new("RGB", (100, 50), "red").save(src)
        out = Path(td) / "a.jpg"
        thumbnail(src, out, size="32x32")
        with Image.open(out) as im:
            assert max(im.size) <= 32
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())