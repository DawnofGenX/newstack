"""Pillow-based thumbnailer."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}


def _parse_size(size: str | tuple[int, int]) -> tuple[int, int]:
    if isinstance(size, str):
        w, h = size.lower().split("x")
        return int(w), int(h)
    return int(size[0]), int(size[1])


def thumbnail(
    src: Path | str,
    dst: Path | str,
    size: str | tuple[int, int] = "128x128",
    quality: int = 85,
    fmt: str | None = None,
) -> Path:
    src_path = Path(src)
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    box = _parse_size(size)
    with Image.open(src_path) as im:
        # EXIF orientation aware
        im = ImageOps.exif_transpose(im)
        # decide output format
        out_fmt = (fmt or dst_path.suffix.lstrip(".") or "JPEG").upper()
        if out_fmt == "JPG":
            out_fmt = "JPEG"
        # handle modes
        if out_fmt == "JPEG":
            if im.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                if im.mode in ("RGBA", "LA"):
                    background.paste(im, mask=im.split()[-1])
                    im = background
                else:
                    im = im.convert("RGB")
            else:
                im = im.convert("RGB")
        elif im.mode == "P":
            im = im.convert("RGBA")
        # resize preserving aspect
        im.thumbnail(box, Image.Resampling.LANCZOS)
        save_kwargs: dict[str, object] = {}
        if out_fmt == "JPEG":
            save_kwargs = {"quality": quality, "subsampling": 0, "optimize": True}
        im.save(dst_path, format=out_fmt, **save_kwargs)
    return dst_path


def process_dir(
    src_dir: Path | str,
    dst_dir: Path | str,
    size: str | tuple[int, int] = "128x128",
    quality: int = 85,
) -> list[dict[str, str]]:
    src = Path(src_dir)
    dst = Path(dst_dir)
    dst.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, str]] = []
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.suffix.lower() not in SUPPORTED:
            continue
        out = dst / (p.stem + ".jpg")
        try:
            thumbnail(p, out, size=size, quality=quality)
            results.append({"file": p.name, "status": "ok", "output": str(out)})
        except Exception as exc:  # noqa: BLE001 - per-file reporting
            results.append({"file": p.name, "status": "error", "error": str(exc)})
    return results