"""Infix in, one integer out: the yard, the oracle, the answer.

to_postfix(expr) answers the postfix token list Dijkstra's yard
yields; evaluate(tokens) reckons a postfix list to the single
integer left standing; value_of(expr) is both at once. The rule
every pop keeps: the operator stack yields only to tighter
binding - * and / park tighter than + and -, every operator binds
left to right, '/' floors. The promise is checked, never
assumed: value_of(expr) equals the shipped recursive-descent
oracle on every shipped and seeded corpus, and evaluate of
to_postfix equals value_of.
"""

from __future__ import annotations

from .calc import (
    evaluate,
    value_of,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Record,
    Snapshot,
    audit,
    load_records,
    report_lines,
    synthetic,
    write_records,
)
from .demo import (
    Story,
    stories,
)
from .expr import (
    CLOSE,
    MAX_EXPR,
    MAX_NUMBER,
    OPEN,
    OPERATORS,
    ExprError,
    Number,
    Op,
    read_expr,
    token_text,
)
from .oracle import (
    descent,
)
from .yard import (
    balanced,
    postfix_text,
    to_postfix,
)

__version__ = "0.1.0"

__all__ = [
    "CLOSE",
    "DEFAULT_SEED",
    "MAX_EXPR",
    "MAX_NUMBER",
    "OPEN",
    "OPERATORS",
    "CorpusError",
    "ExprError",
    "Number",
    "Op",
    "Record",
    "Snapshot",
    "Story",
    "__version__",
    "audit",
    "balanced",
    "descent",
    "evaluate",
    "load_records",
    "postfix_text",
    "read_expr",
    "report_lines",
    "stories",
    "synthetic",
    "to_postfix",
    "token_text",
    "value_of",
    "write_records",
]
