"""An arithmetic parser whose precedence and exactness are both checkable."""

from .evaluator import PRECISION, EvalError, evaluate
from .lexer import LexError, Token, tokenize
from .nodes import Binary, Call, Name, Number, Unary, depth, tree_lines, walk
from .parser import ParseError, parse

__version__ = "0.1.0"

__all__ = [
    "PRECISION",
    "Binary",
    "Call",
    "EvalError",
    "LexError",
    "Name",
    "Number",
    "ParseError",
    "Token",
    "Unary",
    "__version__",
    "depth",
    "evaluate",
    "parse",
    "tokenize",
    "tree_lines",
    "walk",
]
