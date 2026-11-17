import tempfile
from pathlib import Path

from PIL import Image

from {{ package_name }}.thumbnailer import process_dir, thumbnail


def test_basic_dimensions():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "a.png"
        Image.new("RGB", (200, 100), "blue").save(src)
        out = Path(td) / "a.jpg"
        thumbnail(src, out, size="64x64")
        with Image.open(out) as im:
            assert im.size == (64, 32)


def test_exif_orientation():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "b.jpg"
        img = Image.new("RGB", (100, 50), "green")
        exif = img.getexif()
        exif[274] = 6
        img.save(src, exif=exif)
        out = Path(td) / "b.jpg"  # overwrite? use different
        out = Path(td) / "bout.jpg"
        thumbnail(src, out, size="64x64")
        with Image.open(out) as im:
            # transposed to 50x100 then fitted -> 32x64
            assert im.size == (32, 64)


def test_rgba_to_jpeg():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "c.png"
        Image.new("RGBA", (40, 40), (255, 0, 0, 128)).save(src)
        out = Path(td) / "c.jpg"
        thumbnail(src, out, size="20x20")
        with Image.open(out) as im:
            assert im.mode == "RGB"
            assert im.size == (20, 20)


def test_palette_png():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "d.png"
        Image.new("P", (30, 30)).save(src)
        out = Path(td) / "d.png"
        thumbnail(src, out, size="15x15", fmt="PNG")
        with Image.open(out) as im:
            assert im.size == (15, 15)


def test_batch_reports_errors():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src"
        dst = Path(td) / "dst"
        src.mkdir()
        Image.new("RGB", (10, 10)).save(src / "ok.png")
        (src / "bad.txt").write_text("nope")
        res = process_dir(src, dst)
        assert any(r["status"] == "ok" for r in res)
        assert len(res) == 1