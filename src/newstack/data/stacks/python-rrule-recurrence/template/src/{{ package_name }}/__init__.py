"""Recurrence rules expanded into instants, with the reasons attached.

The two entry points are the modules ``expand`` and ``explain``; importing the functions
here would shadow the modules of the same name, and ``from pkg import expand`` would then
hand back a function where every reader expects a module.
"""

from .explain import Decision
from .rrule import ByDay, Rule, RuleError, parse

__all__ = ["ByDay", "Decision", "Rule", "RuleError", "parse"]
__version__ = "0.1.0"
