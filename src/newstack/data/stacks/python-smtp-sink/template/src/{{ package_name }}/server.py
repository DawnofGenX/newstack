"""The SMTP side: aiosmtpd with a handler that never refuses real mail."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass, field
from pathlib import Path

from aiosmtpd.controller import Controller

from .mailbox import Mailbox, Message


def free_port(host: str) -> int:
    """A port nobody holds, for callers that asked for port 0.

    ``Controller(port=0)`` is not usable: aiosmtpd needs a concrete port for the
    "is the server up yet" probe, so it connects to 0 and raises
    ConnectionRefusedError from start(). Bind and release one first.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return int(probe.getsockname()[1])


# aiosmtpd answers 552 itself when the message exceeds data_size_limit, so the
# limit is a Controller argument and not something the handler checks.
DEFAULT_LIMIT = 256 * 1024


@dataclass
class SinkConfig:
    host: str = "127.0.0.1"
    port: int = 8025
    root: Path = Path("mailbox")
    size_limit: int = DEFAULT_LIMIT
    reject_recipients: tuple[str, ...] = ()
    received: list[Message] = field(default_factory=list)


class SinkHandler:
    """Store every accepted message; refuse only what policy names."""

    def __init__(self, mailbox: Mailbox, config: SinkConfig) -> None:
        self.mailbox = mailbox
        self.config = config
        self.refused: list[tuple[str, str]] = []

    async def handle_DATA(self, server, session, envelope):  # noqa: N802 - aiosmtpd API
        for recipient in envelope.rcpt_tos:
            if recipient.lower() in {bad.lower() for bad in self.config.reject_recipients}:
                self.refused.append((recipient, "policy"))
                return "550 mailbox unavailable"
        message = self.mailbox.store(
            envelope.mail_from or "",
            list(envelope.rcpt_tos),
            envelope.original_content or b"",
        )
        self.config.received.append(message)
        return "250 Message accepted for delivery"


class Sink:
    """A started SMTP server plus the mailbox it feeds."""

    def __init__(self, config: SinkConfig | None = None) -> None:
        self.config = config or SinkConfig()
        self.mailbox = Mailbox(self.config.root)
        self.handler = SinkHandler(self.mailbox, self.config)
        self._port = self.config.port or free_port(self.config.host)
        # enable_SMTPUTF8: a sink that refuses 8-bit headers cannot capture
        # mail from anyone who writes an accented name.
        self.controller = Controller(
            self.handler,
            hostname=self.config.host,
            port=self._port,
            data_size_limit=self.config.size_limit,
            enable_SMTPUTF8=True,
        )
        self._started = False

    @property
    def port(self) -> int:
        """The bound port, which matters when the caller asked for 0."""
        return self._port

    def start(self) -> Sink:
        self.controller.start()
        self._started = True
        return self

    def stop(self) -> None:
        if self._started:
            self.controller.stop()
            self._started = False

    def wait(self) -> None:
        """Block until the event loop is interrupted, then stop cleanly."""
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            self.stop()

    def __enter__(self) -> Sink:
        return self.start()

    def __exit__(self, *exc_info: object) -> None:
        self.stop()
