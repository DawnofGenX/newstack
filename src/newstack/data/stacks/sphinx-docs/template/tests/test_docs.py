"""The docs are part of the product, so they are tested like code.

The site is built into a temporary directory with warnings promoted to errors: a broken
cross-reference or a module that stopped importing fails here rather than publishing a
page full of "TODO" placeholders.
"""

from pathlib import Path

import pytest
from sphinx.application import Sphinx

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("html")
    app = Sphinx(
        srcdir=str(ROOT / "docs"),
        confdir=str(ROOT / "docs"),
        outdir=str(out),
        doctreedir=str(out / ".doctrees"),
        buildername="html",
        warningiserror=True,
        freshenv=True,
        status=None,
        warning=None,
    )
    app.build()
    return out


def test_the_api_reference_is_generated_from_the_package(site: Path) -> None:
    html = (site / "api.html").read_text(encoding="utf-8")
    assert "count_text" in html
    assert "Counts" in html


def test_the_guide_is_reachable_from_the_index(site: Path) -> None:
    index = (site / "index.html").read_text(encoding="utf-8")
    assert "guides/counting.html" in index


def test_doctest_output_is_rendered_in_the_guide(site: Path) -> None:
    html = (site / "guides" / "counting.html").read_text(encoding="utf-8")
    # The byte count from the doctest, which only appears if the example ran and matched.
    assert "héllo" in html
    assert "14" in html
