from pathlib import Path

from {{ package_name }}.extract import extract_cards, extract_tables


def test_tables_fixture() -> None:
    html = Path("fixtures/sample.html").read_text(encoding="utf-8")
    tables = extract_tables(html)
    assert len(tables) == 1
    assert len(tables[0]) == 3
    assert tables[0][0] == {"name": "apple", "qty": "3"}


def test_cards_fixture() -> None:
    html = Path("fixtures/sample.html").read_text(encoding="utf-8")
    cards = extract_cards(html)
    assert len(cards) == 2
    assert cards[0]["title"] == "Card A"
