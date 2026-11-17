"""Convenience alias for stack discovery.

The registry module owns the real implementation; this module re-exports it so
callers (including ``scripts/gen_catalog.py``) can write
``from newstack.stacks import load_stacks``.
"""

from .registry import Stack, get_stack, load_catalog, load_stacks, search_roots

__all__ = ["Stack", "get_stack", "load_catalog", "load_stacks", "search_roots"]
