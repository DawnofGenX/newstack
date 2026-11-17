"""openpyxl report builder."""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def _convert(value: str) -> object:
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return value


def build_report(rows: list[dict[str, object]], out_path: Path | str, title: str = "Report") -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = title

    if not rows:
        wb.save(out)
        return out

    headers = list(rows[0].keys())
    ws.append(headers)

    # header style
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(bold=True, color="FFFFFF")
    for col_idx, _h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row in rows:
        ws.append([row.get(h) for h in headers])

    last_data_row = ws.max_row

    # number formats for numeric columns
    numeric_cols: list[int] = []
    for col_idx, h in enumerate(headers, start=1):
        is_num = False
        for r in range(2, last_data_row + 1):
            val = ws.cell(row=r, column=col_idx).value
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                is_num = True
                ws.cell(row=r, column=col_idx).number_format = "#,##0.00"
        if is_num:
            numeric_cols.append(col_idx)

    # totals row
    total_row = last_data_row + 1
    ws.cell(row=total_row, column=1, value="Total")
    ws.cell(row=total_row, column=1).font = Font(bold=True)
    for col_idx in numeric_cols:
        letter = get_column_letter(col_idx)
        ws.cell(row=total_row, column=col_idx, value=f"=SUM({letter}2:{letter}{last_data_row})")

    # freeze panes, autofilter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{last_data_row}"

    # column widths
    for col_idx, h in enumerate(headers, start=1):
        max_len = len(str(h))
        for r in range(2, last_data_row + 1):
            val = ws.cell(row=r, column=col_idx).value
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[get_column_letter(col_idx)].width = max_len + 2

    wb.save(out)
    return out


def read_csv(path: Path | str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            rows.append({k: _convert(v) for k, v in (raw or {}).items()})
    return rows