import tempfile
from pathlib import Path

from {{ package_name }}.store import Store


def test_dedupe_does_not_grow_store():
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "s")
        store.put(b"same", name="a")
        before = store.blob_count()
        store.put(b"same", name="b")
        after = store.blob_count()
        assert before == after == 1
        assert store.total_bytes() == 4


def test_atomic_write_and_get():
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "s")
        digest = store.put(b"payload", name="x")
        assert len(digest) == 64
        assert store.get("x") == b"payload"
        assert store.verify()["ok"]


def test_gc_leaves_referenced():
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "s")
        store.put(b"keep", name="keep")
        store.put(b"drop", name="drop")
        store.delete("drop")
        freed = store.gc()
        assert freed == 4
        assert store.blob_count() == 1
        assert store.verify()["ok"]


def test_verify_detects_corruption():
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "s")
        store.put(b"keep", name="keep")
        # corrupt blob
        digest = store._manifest["keep"]
        blob = store._blob_path(digest)
        blob.write_bytes(b"nope")
        res = store.verify()
        assert not res["ok"]
        assert res["errors"]