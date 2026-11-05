"""`python -m {{ package_name }}` is the CLI."""

from {{ package_name }}.cli import main

raise SystemExit(main())
