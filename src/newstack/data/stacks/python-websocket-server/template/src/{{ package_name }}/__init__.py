"""A zero-dependency RFC 6455 WebSocket service.

This package holds the handshake, the frame codec and the JSON protocol.
"""

from .client import WSClient, connect
from .protocol import count_stats, dispatch
from .server import DEFAULT_HOST, DEFAULT_PORT, make_server, serve

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "WSClient",
    "connect",
    "count_stats",
    "dispatch",
    "make_server",
    "serve",
]
