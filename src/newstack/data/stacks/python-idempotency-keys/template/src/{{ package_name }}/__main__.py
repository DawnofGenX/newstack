"""Entry point for python -m: the same code the console script calls."""

from .cli import main

raise SystemExit(main())
