# {{ title }}

{{ description }}

A Sphinx documentation site whose subject is a small Python package, so the whole
pipeline is real: `autodoc` reads the docstrings out of `src/{{ package_name }}/`, the
examples in the guide are executed as doctests, and the build runs with `-W` so a broken
cross-reference or an unimportable module fails CI instead of publishing.

The docs are also tested like code: `tests/test_docs.py` builds the site into a temporary
directory with warnings promoted to errors and asserts the API page and the guide exist.

## Develop

```bash
uv sync --group dev
uv run sphinx-build -b html docs docs/_build/html   # open docs/_build/html/index.html
uv run python -m sphinx -b html -a -E docs docs/_build/html   # no-cache rebuild
```

## Check

```bash
uv run python -m sphinx -W --keep-going -b html docs docs/_build/html   # warnings are errors
uv run python -m sphinx -b doctest docs docs/_build/doctest             # run the examples
uv run pytest                                                          # package + docs tests
uv run ruff check .
```

## Layout

- `docs/conf.py` — autodoc + doctest + viewcode, `sys.path` pointed at `src/`, so the
  documented package is the one the wheel is built from.
- `docs/index.rst` — landing page and the toctrees that make every page reachable.
- `docs/guides/counting.rst` — the prose guide; its `.. doctest::` blocks are executed.
- `docs/api.rst` — `automodule`, so function signatures and docstrings come from the code.
- `src/{{ package_name }}/counters.py` — `count_text(text) -> Counts`, `wc` semantics.
- `tests/test_docs.py` — builds the site with `warningiserror=True` and asserts the pages.

`nitpicky = True` in `docs/conf.py` turns a dangling reference into a warning, and `-W`
turns that warning into a failed build — the two settings are only useful together.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
