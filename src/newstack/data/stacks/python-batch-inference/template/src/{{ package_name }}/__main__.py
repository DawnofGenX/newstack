"""`python -m {{ package_name }}` entry point."""

import sys

from {{ package_name }}.cli import main

if __name__ == "__main__":
    sys.exit(main())
