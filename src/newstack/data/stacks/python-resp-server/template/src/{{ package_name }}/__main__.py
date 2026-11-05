"""Run the same entry point as the console script."""

from __future__ import annotations

import sys

from .cli import main

sys.exit(main())
