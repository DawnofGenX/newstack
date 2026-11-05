# {{ title }}

Deterministic reports over CSV and Parquet files, using DuckDB. One command,
one markdown table, the same bytes every run.

```bash
uv venv --quiet && uv pip install --python .venv/bin/python -e .
.venv/bin/python -m {{ package_name }} report \
  --data data/orders.csv --group-by region --metric revenue
```

```
# revenue by region

| region | total revenue | rows |
| --- | ---: | ---: |
| south | 550.49 | 3 |
| west | 470.10 | 2 |
| north | 410.50 | 3 |
| east | 175.25 | 3 |

rows 12 · groups 4 · null revenue skipped 1
```

## Why each of those lines is there

- **Decimal, not float.** Revenue is summed as `DECIMAL(18, 4)`. `0.1 + 0.2` is
  not `0.3` in binary floating point, and a report that is wrong in the last
  digit is worse than no report.
- **Nulls are counted, never dropped.** The footer says how many rows were left
  out, so "sum of revenue" cannot silently become "sum of the revenue we could
  parse".
- **The order is fixed.** Groups are sorted by total, ties broken by the group
  name, so a diff between two runs shows what changed and nothing else.
- **Identifiers are checked before they are interpolated.** DuckDB cannot bind a
  column name as a parameter, so `Dataset.column()` checks the name against the
  file's own `DESCRIBE` output and quotes what it returns; an unknown column
  exits 2 with the real names in the message.
- **Exit codes**: `0` a report was produced, `2` the file or the request cannot
  be served. Never `1` — a report over bad input is not a partial success.

`--format json|csv` renders the same numbers, `--limit N` keeps the top N groups
(the skip count still covers the whole file), and `--out FILE` writes instead of
printing.

```bash
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} selftest
PY=.venv/bin/python bash smoke.sh   # diffs the report against expected/report.md
```
