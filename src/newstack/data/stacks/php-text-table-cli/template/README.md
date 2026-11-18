# {{ npm_name }}

{{ description }}

Renders CSV or TSV as an aligned text table: automatic column widths, per-column
alignment, wide-character aware padding, an optional header row and optional
truncation.

## Usage

```bash
# a header row, ASCII borders
printf 'name,score\nalice,3\nbob,12\n' | {{ npm_name }} --header

# right-align the numeric column, no borders, tab separated
{{ npm_name }} --header --border none --align-column 1=right --delimiter tab < report.tsv

# truncate long cells
{{ npm_name }} --max-width 20 < long.csv
```

```
+-------+-------+
| name  | score |
+-------+-------+
| alice | 3     |
| bob   | 12    |
+-------+-------+
```

Exit codes: `0` ok, `1` unreadable file, empty input or malformed CSV, `2` bad
usage.

The table renderer works without the CLI:

```php
use {{ package_name }}\Table;

echo Table::make([['alice', '3']], ['name', 'score'])
    ->alignments([Table::ALIGN_LEFT, Table::ALIGN_RIGHT])
    ->render();
```
