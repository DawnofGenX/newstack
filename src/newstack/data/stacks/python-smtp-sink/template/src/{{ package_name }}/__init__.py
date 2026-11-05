"""A local SMTP sink for development: accept mail, keep it, list it."""

from __future__ import annotations

from .mailbox import Mailbox, Message
from .server import Sink, SinkConfig

__all__ = ["Mailbox", "Message", "Sink", "SinkConfig"]
