"""{{ title }} package."""

from .app import create_app
from .stats import analyze

__all__ = ["analyze", "create_app"]