"""Structured JSON logging."""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

SENSITIVE_SUBSTRINGS = ("password", "token", "authorization", "secret", "api_key", "apikey")


def _is_sensitive(key: str) -> bool:
    low = key.lower()
    return any(s in low for s in SENSITIVE_SUBSTRINGS)


def _redact_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if _is_sensitive(str(k)):
                out[k] = "[REDACTED]"
            else:
                out[k] = _redact_obj(v)
        return out
    if isinstance(obj, list):
        return [_redact_obj(x) for x in obj]
    return obj


class JsonLogger:
    def __init__(
        self,
        name: str = "root",
        level: str | int = "INFO",
        output: Any = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.level = LEVELS.get(str(level).upper(), 20) if isinstance(level, str) else int(level)
        self.output = output if output is not None else sys.stdout
        self.context = dict(context or {})

    def _enabled(self, level: str) -> bool:
        return LEVELS[level] >= self.level

    def bind(self, **kwargs: Any) -> JsonLogger:
        merged = dict(self.context)
        merged.update(kwargs)
        child = JsonLogger(name=self.name, level=self.level, output=self.output, context=merged)
        return child

    def child(self, name: str, **kwargs: Any) -> JsonLogger:
        merged = dict(self.context)
        merged.update(kwargs)
        return JsonLogger(name=f"{self.name}.{name}", level=self.level, output=self.output, context=merged)

    def _emit(self, level: str, message: str, exc_info: Any = None, **extra: Any) -> None:
        if not self._enabled(level):
            return
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
        }
        # context first
        for k, v in self.context.items():
            if k not in record:
                record[k] = v
        # extra
        for k, v in extra.items():
            record[k] = v
        if exc_info:
            ei = exc_info if exc_info is not True else None
            if ei is None:
                ei = sys.exc_info()
            if isinstance(ei, BaseException):
                ei = (type(ei), ei, ei.__traceback__)
            if ei and ei[0] is not None:
                tb = "".join(traceback.format_exception(ei[0], ei[1], ei[2]))
                record["exception"] = {
                    "type": ei[0].__name__,
                    "message": str(ei[1]),
                    "traceback": tb,
                }
        record = _redact_obj(record)
        line = json.dumps(record, ensure_ascii=False)
        self.output.write(line + "\n")
        if hasattr(self.output, "flush"):
            self.output.flush()

    def debug(self, message: str, **extra: Any) -> None:
        self._emit("DEBUG", message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        self._emit("INFO", message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        self._emit("WARNING", message, **extra)

    def error(self, message: str, exc_info: Any = None, **extra: Any) -> None:
        self._emit("ERROR", message, exc_info=exc_info, **extra)

    def exception(self, message: str, **extra: Any) -> None:
        self._emit("ERROR", message, exc_info=True, **extra)

    def critical(self, message: str, **extra: Any) -> None:
        self._emit("CRITICAL", message, **extra)


redact = _redact_obj