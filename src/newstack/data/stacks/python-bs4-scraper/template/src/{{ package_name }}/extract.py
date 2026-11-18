"""HTML extraction helpers."""

from __future__ import annotations

import csv
import io

from bs4 import BeautifulSoup


def extract_tables(html: str) -> list[list[dict[str, str]]]:
    soup = BeautifulSoup(html, "html.parser")
    tables: list[list[dict[str, str]]] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            tables.append([])
            continue
        header_cells = rows[0].find_all(["th", "td"])
        headers = [cell.get_text(strip=True) for cell in header_cells]
        is_header = bool(header_cells) and all(cell.name == "th" for cell in header_cells)
        if is_header:
            data_rows = rows[1:]
        else:
            data_rows = rows
            headers = [f"col{i}" for i in range(len(headers))]
        parsed: list[dict[str, str]] = []
        for tr in data_rows:
            cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
            if not cells:
                continue
            while len(cells) < len(headers):
                cells.append("")
            parsed.append(dict(zip(headers, cells)))
        tables.append(parsed)
    return tables


def extract_cards(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    cards: list[dict[str, str]] = []
    for card in soup.select(".card"):
        title_el = card.select_one(".title")
        cards.append(
            {
                "title": title_el.get_text(strip=True) if title_el else "",
                "text": card.get_text(" ", strip=True),
            }
        )
    return cards


def tables_to_csv(tables: list[list[dict[str, str]]]) -> str:
    if not tables or not tables[0]:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(tables[0][0].keys()))
    writer.writeheader()
    for row in tables[0]:
        writer.writerow(row)
    return buf.getvalue()
