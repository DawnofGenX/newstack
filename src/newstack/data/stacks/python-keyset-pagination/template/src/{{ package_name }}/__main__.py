"""`python -m` entry point: the same code the console script calls."""

from .cli import main

raise SystemExit(main())
