"""Entry point so `python -m` runs exactly what the console script runs."""

from .cli import main

raise SystemExit(main())
