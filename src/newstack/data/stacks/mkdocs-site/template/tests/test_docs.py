"""The site is built in CI with warnings promoted to errors, so build it here too."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("site")
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(out)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return out


def test_the_guide_is_linked_from_the_home_page(site: Path) -> None:
    index = (site / "index.html").read_text(encoding="utf-8")
    assert "guide/counting/" in index


def test_the_reference_page_is_rendered(site: Path) -> None:
    reference = (site / "reference" / "api" / "index.html").read_text(encoding="utf-8")
    assert "count_text" in reference
    assert "Counts" in reference


def test_the_executed_example_output_is_in_the_guide(site: Path) -> None:
    guide = (site / "guide" / "counting" / "index.html").read_text(encoding="utf-8")
    assert "héllo" in guide
    assert "bytes=14" in guide
