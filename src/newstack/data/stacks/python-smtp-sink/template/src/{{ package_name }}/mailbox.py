"""Where captured mail goes.

One readable ``.eml`` per message plus one JSON line in ``index.ndjson``. The
index is append-only so a crash loses at most the message being written, and
``--dump`` can rebuild every fact from the files if the index is removed.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Message:
    id: str
    sender: str
    recipients: tuple[str, ...]
    size: int
    sha256: str
    subject: str
    received_at: str
    path: str

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["recipients"] = list(self.recipients)
        return payload


def _header_lines(raw: bytes) -> list[bytes]:
    """Return the header block as raw lines, stopping at the first blank line."""
    head, _, _ = raw.partition(b"\r\n\r\n")
    if not head:
        head, _, _ = raw.partition(b"\n\n")
    return head.splitlines()


def subject_of(raw: bytes) -> str:
    """The Subject header, unfolded, decoded to text where possible.

    Not a MIME parser: a sink only needs one line a human can read, and pulling
    in a parser to get it would hide the fact that the stored message is the
    authority.
    """
    lines = _header_lines(raw)
    collected: list[bytes] = []
    collecting = False
    for line in lines:
        if collecting and line[:1] in (b" ", b"\t"):
            collected.append(line.strip())
            continue
        if collecting:
            break
        if line.lower().startswith(b"subject:"):
            collected.append(line.split(b":", 1)[1].strip())
            collecting = True
    if not collected:
        return ""
    joined = b" ".join(collected)
    try:
        from email.header import decode_header, make_header

        return str(make_header(decode_header(joined.decode("utf-8", "replace"))))
    except Exception:  # pragma: no cover - a header cannot break the sink
        return joined.decode("utf-8", "replace")


class Mailbox:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.ndjson"

    def _next_id(self) -> str:
        return f"{time.time_ns():020d}"

    def store(self, sender: str, recipients: list[str], raw: bytes) -> Message:
        digest = hashlib.sha256(raw).hexdigest()
        message_id = self._next_id()
        name = f"{message_id}-{digest[:8]}.eml"
        target = self.root / name
        # Write then rename: a reader must never see a half-written message.
        temporary = target.with_suffix(".eml.part")
        temporary.write_bytes(raw)
        os.replace(temporary, target)

        message = Message(
            id=message_id,
            sender=sender,
            recipients=tuple(recipients),
            size=len(raw),
            sha256=digest,
            subject=subject_of(raw),
            received_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            path=name,
        )
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message.as_dict(), ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return message

    def messages(self) -> list[Message]:
        """Read the index back, newest last. A torn last line is ignored."""
        if not self.index_path.exists():
            return []
        found: list[Message] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            found.append(
                Message(
                    id=record["id"],
                    sender=record["sender"],
                    recipients=tuple(record["recipients"]),
                    size=record["size"],
                    sha256=record["sha256"],
                    subject=record["subject"],
                    received_at=record["received_at"],
                    path=record["path"],
                )
            )
        return found

    def count(self) -> int:
        return len(self.messages())

    def rebuild_index(self) -> int:
        """Recreate ``index.ndjson`` from the ``.eml`` files on disk."""
        rewritten = 0
        if self.index_path.exists():
            self.index_path.unlink()
        for path in sorted(self.root.glob("*.eml")):
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            message_id = path.name.split("-", 1)[0]
            message = Message(
                id=message_id,
                sender="",
                recipients=(),
                size=len(raw),
                sha256=digest,
                subject=subject_of(raw),
                received_at=time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime)
                ),
                path=path.name,
            )
            with self.index_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(message.as_dict(), ensure_ascii=False) + "\n")
            rewritten += 1
        return rewritten
