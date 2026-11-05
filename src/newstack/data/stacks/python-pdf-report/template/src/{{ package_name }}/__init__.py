"""Render a deterministic PDF report of text statistics."""

from .counts import Counts, count_text
from .model import InputError, Record, parse_ndjson, read_records
from .render import Summary, build_report

__all__ = [
    "Counts",
    "InputError",
    "Record",
    "Summary",
    "build_report",
    "count_text",
    "parse_ndjson",
    "read_records",
]
