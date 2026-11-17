import tempfile
from pathlib import Path

from openpyxl import load_workbook

from {{ package_name }}.report import build_report


def test_cells_values_and_formula():
    rows = [{"product": "pen", "qty": 2, "price": 1.5}, {"product": "cup", "qty": 3, "price": 2.0}]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "r.xlsx"
        build_report(rows, out)
        wb = load_workbook(out)
        ws = wb.active
        assert ws["A1"].value == "product"
        assert ws["A2"].value == "pen"
        assert ws["B2"].value == 2
        # number format
        assert ws["C2"].number_format == "#,##0.00"
        # total row formula
        total_row = 4
        assert ws.cell(row=total_row, column=3).value == "=SUM(C2:C3)"
        # freeze panes
        assert ws.freeze_panes == "A2"
        # autofilter
        assert ws.auto_filter.ref == "A1:C3"


def test_styles():
    rows = [{"a": 1}]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "r.xlsx"
        build_report(rows, out)
        wb = load_workbook(out)
        ws = wb.active
        assert ws["A1"].font.bold is True
        assert ws.column_dimensions["A"].width is not None