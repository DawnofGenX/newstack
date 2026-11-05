# {{ title }}

{{ description }}

An analytics-engineering project on [dbt](https://docs.getdbt.com) + DuckDB: a seed CSV, a
staging model that types and normalises it, a mart that computes `wc`-compatible counts in
SQL, and tests that make the numbers load-bearing. `dbt build` runs the models **and** the
tests, so there is one command that either proves the pipeline or fails.

This scaffold asks for **Python {{ python_version }} or newer** (dbt-core 1.12 supports it)
and its CI runs every version in the same list.

## Develop

```bash
uv sync                                  # .venv with dbt-duckdb and ruff
.venv/bin/dbt build --profiles-dir .     # seed → staging → mart, then every test
.venv/bin/dbt docs generate --profiles-dir .   # target/ has a browsable catalog
```

`profiles.yml` is committed: the only target is a local DuckDB file under `target/`, so
there is no credential to hide. That is also why every command passes `--profiles-dir .`.

## The pipeline

| Layer | File | What it does |
| --- | --- | --- |
| seed | `seeds/documents.csv` | Source data. Newlines are stored as the two characters `\` + `n`, because quoting a multi-line field in a CSV is how seed files get corrupted in review. |
| staging | `models/staging/stg_documents.sql` | Restores real newlines (`replace(raw_text, '\n', chr(10))`), renames nothing else. A view. |
| marts | `models/marts/doc_stats.sql` | Adds `lines`, `words`, `bytes`. A table. |

The counts are the `wc` definitions, in SQL: `lines` is the number of `chr(10)` characters,
`words` is `len(regexp_extract_all(text, '\S+'))`, and `bytes` is `strlen(text)` — DuckDB's
`length()` counts **characters** and `strlen()` counts **bytes**, so `héllo wörld\n` is 12
characters and 14 bytes. Getting that backwards is the classic analytics bug.

| id | text | lines | words | bytes |
| --- | --- | --- | --- | --- |
| 1 | `hello world\n` | 1 | 2 | 12 |
| 2 | `a b\nc\n` | 2 | 3 | 6 |
| 3 | `  padded  \n` | 1 | 1 | 11 |
| 4 | `héllo wörld\n` | 1 | 2 | 14 |

## Tests

- Generic tests in `models/marts/schema.yml`: `unique` and `not_null` on `id`, `not_null`
  everywhere else. They run inside `dbt build`.
- A **singular** test, `tests/assert_counts_match_expected.sql`, fails by returning rows, so
  it encodes the table above rather than trusting a description. Changing a model's maths
  fails the build, not a dashboard.
- `scripts/check_counts.py` reads the built DuckDB file directly and re-asserts the same
  numbers. It exists because `dbt test` and the mart are one system: a hand-written query
  against the file is the only check that does not share code with the thing under test.

```bash
.venv/bin/python scripts/check_counts.py
.venv/bin/ruff check .
```

## Layout

- `dbt_project.yml` — paths, materialisations, seed column types.
- `profiles.yml` — the DuckDB target (local file, no secrets).
- `pyproject.toml` — the dbt-duckdb and ruff pins; `[tool.uv] package = false` because the
  project is data, not a wheel.
- `seeds/`, `models/staging/`, `models/marts/`, `tests/` — the pipeline.
- `scripts/check_counts.py` — the independent read-only assertion.
- `target/` — build output and the DuckDB file; ignored, never committed.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
