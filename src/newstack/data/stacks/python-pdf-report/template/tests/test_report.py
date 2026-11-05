"""The two properties that make this report trustworthy: correct counts, and the
same bytes for the same input. Both are checked by reading the PDF back."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from {{ package_name }}.cli import main
from {{ package_name }}.counts import count_text
from {{ package_name }}.model import (
    InputError,
    Record,
    parse_ndjson,
    read_records,
)
from {{ package_name }}.render import build_report


def extract(pdf: bytes) -> tuple[str, int]:
    reader = PdfReader(__import__("io").BytesIO(pdf))
    return "\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages)


def test_count_text_counts_newlines_not_lines_of_output() -> None:
    counts = count_text("a b\nc\n")
    assert (counts.lines, counts.words, counts.byte_count) == (2, 3, 6)


def test_count_text_counts_utf8_bytes_not_characters() -> None:
    counts = count_text("héllo wörld\n")
    assert (counts.lines, counts.words, counts.byte_count) == (1, 2, 14)
    assert len("héllo wörld\n") == 12, "the character count is a different number on purpose"


def test_every_ascii_separator_ends_a_word() -> None:
    counts = count_text("a\tb\vc\fd\re")
    assert counts.words == 5
    assert counts.lines == 0, "carriage return is a separator, not a newline"


def test_empty_input_counts_zero() -> None:
    counts = count_text("")
    assert counts.as_dict() == {"lines": 0, "words": 0, "bytes": 0}


def test_parse_skips_blank_lines_and_a_missing_trailing_newline() -> None:
    records = parse_ndjson('{"id": "one", "text": "a"}\n\n{"id": "two", "text": "b"}')
    assert [record.id for record in records] == ["one", "two"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ('{"id": "one", "text": "a"}\n{oops\n', "line 2: not JSON"),
        ('{"text": "a"}\n', 'line 1: "id" must be a non-empty string'),
        ('{"id": "one", "text": 42}\n', 'line 1: "text" must be a string'),
        ('{"id": "one", "text": "a"}\n{"id": "one", "text": "b"}\n', "line 2: duplicate id"),
        ("[1, 2, 3]\n", "line 1: expected a JSON object"),
    ],
)
def test_parse_names_the_line_that_broke(payload: str, message: str) -> None:
    with pytest.raises(InputError) as caught:
        parse_ndjson(payload)
    assert message in str(caught.value)


def test_read_records_reports_non_utf8_rather_than_mangling_it(tmp_path: Path) -> None:
    path = tmp_path / "latin1.ndjson"
    path.write_bytes(b'{"id": "one", "text": "caf\xe9"}\n')
    with pytest.raises(InputError) as caught:
        read_records(path)
    assert "not UTF-8" in str(caught.value)


def test_read_records_reports_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InputError) as caught:
        read_records(tmp_path / "absent.ndjson")
    assert "absent.ndjson" in str(caught.value)


def test_the_same_input_produces_the_same_bytes() -> None:
    records = [Record(id="a", text="one\n"), Record(id="b", text="two\n")]
    first, _ = build_report(records, title="Same")
    second, _ = build_report(records, title="Same")
    assert first == second, "a report that differs run to run cannot be diffed or cached"


def test_the_pdf_reads_back_with_every_row_and_the_totals() -> None:
    records = [
        Record(id="alpha", text="a b\nc\n"),
        Record(id="beta", text="héllo wörld\n"),
        Record(id="gamma", text="one two three"),
    ]
    pdf, summary = build_report(records, title="Probe", subtitle="three records")
    text, pages = extract(pdf)
    assert pages == 1
    assert summary.as_dict() == {
        "records": 3,
        "lines": 3,
        "words": 8,
        "bytes": 33,
        "unmappable": 0,
        "pages": 1,
    }
    for row in ("alpha", "beta", "gamma"):
        assert row in text
    assert "totals: 3 lines, 8 words, 33 bytes" in text
    assert "3 record(s)" in text


def test_metadata_is_fixed_so_the_bytes_stay_stable() -> None:
    pdf, _ = build_report([Record(id="a", text="x")], title="Stable")
    metadata = PdfReader(__import__("io").BytesIO(pdf)).metadata
    assert metadata["/Title"] == "Stable"
    assert metadata["/Creator"] == "blog-report"
    # invariant=1 pins the date; a wall-clock stamp would change the bytes per run.
    assert metadata["/CreationDate"].startswith("D:20000101")


def test_characters_the_builtin_font_cannot_draw_are_counted_not_hidden() -> None:
    pdf, summary = build_report([Record(id="日本語", text="x")])
    text, _ = extract(pdf)
    assert summary.unmappable == 3
    assert "???" in text, "the report says a character was dropped; it must not look complete"
    assert "outside the built-in font" in text


def test_per_page_zero_omits_the_table_but_keeps_the_totals() -> None:
    pdf, _ = build_report([Record(id="alpha", text="a b\n")], per_page=0)
    text, _ = extract(pdf)
    assert "alpha" not in text
    assert "totals: 1 lines, 2 words, 4 bytes" in text


def test_cli_writes_the_file_and_prints_a_json_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "records.ndjson"
    source.write_text('{"id": "one", "text": "a b\\n"}\n', encoding="utf-8")
    output = tmp_path / "report.pdf"
    exit_code = main(
        ["--input", str(source), "--output", str(output), "--title", "CLI", "--json"]
    )
    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["records"] == 1
    assert summary["lines"] == 1
    assert summary["output"] == str(output)
    assert output.read_bytes().startswith(b"%PDF-")


def test_cli_refuses_bad_input_with_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "bad.ndjson"
    source.write_text("{oops\n", encoding="utf-8")
    exit_code = main(["--input", str(source), "--output", str(tmp_path / "x.pdf")])
    assert exit_code == 2
    assert "line 1: not JSON" in capsys.readouterr().err
    assert not (tmp_path / "x.pdf").exists(), "a refused input must not leave a partial PDF"
