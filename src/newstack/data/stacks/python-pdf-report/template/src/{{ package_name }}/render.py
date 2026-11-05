"""Building the PDF.

Two properties matter more than layout: the same input must produce the same bytes
(so a diff means a real change), and text the built-in fonts cannot encode must be
counted rather than silently dropped.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from reportlab import rl_config

# MUST be set before any canvas is created. With invariant=1 reportlab stops
# stamping /CreationDate with the wall clock and stops generating random object
# ids, which is the difference between a reproducible report and one that differs
# on every run for no reason.
rl_config.invariant = 1

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .counts import count_text  # noqa: E402
from .model import Record  # noqa: E402

# The standard Type1 fonts are WinAnsi-encoded; anything outside that range is
# drawn as a black box AND extracts as garbage. cp1252 is the same repertoire.
WINANSI = "cp1252"


@dataclass
class Summary:
    records: int
    lines: int
    words: int
    bytes: int
    unmappable: int
    pages: int

    def as_dict(self) -> dict[str, int]:
        return {
            "records": self.records,
            "lines": self.lines,
            "words": self.words,
            "bytes": self.bytes,
            "unmappable": self.unmappable,
            "pages": self.pages,
        }


def sanitize(text: str) -> tuple[str, int]:
    """Replace characters the built-in font cannot encode; return how many."""
    pieces: list[str] = []
    dropped = 0
    for char in text:
        try:
            char.encode(WINANSI)
        except UnicodeEncodeError:
            pieces.append("?")
            dropped += 1
        else:
            pieces.append(char)
    return "".join(pieces), dropped


def build_report(
    records: list[Record],
    *,
    title: str = "Text statistics",
    subtitle: str = "",
    per_page: int = 25,
) -> tuple[bytes, Summary]:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="blog-report",
        subject="Text statistics",
        creator="blog-report",
    )
    styles = getSampleStyleSheet()
    heading = styles["Title"]
    body = ParagraphStyle("body", parent=styles["BodyText"], leading=14)

    totals = {"lines": 0, "words": 0, "bytes": 0}
    unmappable = 0
    rows: list[list[str]] = [["id", "lines", "words", "bytes"]]
    for record in records:
        counts = count_text(record.text)
        clean, dropped = sanitize(record.id)
        unmappable += dropped
        totals["lines"] += counts.lines
        totals["words"] += counts.words
        totals["bytes"] += counts.byte_count
        rows.append([clean, str(counts.lines), str(counts.words), str(counts.byte_count)])

    table = Table(rows, colWidths=[90 * mm, 25 * mm, 25 * mm, 25 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONT", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#94a3b8")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story: list[object] = [Paragraph(sanitize(title)[0], heading)]
    if subtitle:
        story.append(Paragraph(sanitize(subtitle)[0], body))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"{len(records)} record(s)", body))
    story.append(Spacer(1, 3 * mm))
    if per_page > 0:
        story.append(table)
    summary_line = (
        f"totals: {totals['lines']} lines, {totals['words']} words, {totals['bytes']} bytes"
    )
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(summary_line, body))
    if unmappable:
        # Refusing to hide this is the point: a report that quietly renders boxes
        # looks finished and is wrong.
        story.append(
            Paragraph(
                f"{unmappable} character(s) outside the built-in font were replaced with '?'",
                body,
            )
        )
    if per_page > 0 and len(records) > per_page:
        story.append(PageBreak())

    def footer(canvas, doc) -> None:  # noqa: ANN001 - reportlab callback signature
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(18 * mm, 12 * mm, "blog-report")
        canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    summary = Summary(
        records=len(records),
        lines=totals["lines"],
        words=totals["words"],
        bytes=totals["bytes"],
        unmappable=unmappable,
        pages=document.page,
    )
    return buffer.getvalue(), summary
