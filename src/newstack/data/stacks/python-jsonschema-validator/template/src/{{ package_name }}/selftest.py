"""Offline self-test."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .validator import validate_document


def run() -> int:
    schema = {"type": "object", "properties": {"age": {"type": "integer", "minimum": 0}}, "required": ["age"]}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "d.json"
        p.write_text(json.dumps({"age": -1}))
        errs = validate_document({"age": -1}, schema)
        assert errs
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())