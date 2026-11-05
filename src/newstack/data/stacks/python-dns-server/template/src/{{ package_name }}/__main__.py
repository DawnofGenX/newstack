"""Run the same entry point as the console script."""

import sys

from .cli import main

raise SystemExit(main(sys.argv[1:]))
