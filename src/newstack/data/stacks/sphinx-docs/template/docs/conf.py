"""Sphinx configuration for {{ title }}.

The package is imported from `src/`, the same layout the wheel is built from, so
`autodoc` documents exactly what ships instead of an installed copy.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

project = "{{ title }}"
author = "{{ author }}"
copyright = "{{ year }}, {{ author }}"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.viewcode",
]

# Every example in the docs is executed by `sphinx -b doctest`, with the package already
# imported, so a snippet that drifts from the code fails the build instead of shipping.
doctest_global_setup = "from {{ package_name }} import count_text"

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# A missing reference is a broken link: fail on it. The verify step builds with -W, so
# warnings are errors and this is enforced rather than merely recorded.
nitpicky = True
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
root_doc = "index"
