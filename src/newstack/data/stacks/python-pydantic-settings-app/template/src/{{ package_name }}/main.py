from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .settings import Settings


def load_settings(
    overrides: dict[str, Any] | None = None,
    env_file: str | Path | None = ".env",
) -> Settings:
    kwargs: dict[str, Any] = {}
    if env_file is not None:
        kwargs["_env_file"] = str(env_file)
    settings = Settings(**kwargs)
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                setattr(settings, key, value)
    return settings


def _selftest() -> int:
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".env").write_text("APP_PORT=9000\n", encoding="utf-8")
        old = os.getcwd()
        os.chdir(root)
        try:
            os.environ.pop("APP_HOST", None)
            os.environ.pop("APP_PORT", None)
            os.environ["APP_HOST"] = "envhost"
            s = load_settings({"port": 9999})
            assert s.host == "envhost", s.host
            assert s.port == 9999, s.port
            # .env precedence over default
            del os.environ["APP_HOST"]
            s2 = load_settings()
            assert s2.port == 9000, s2.port
            assert s2.host == "127.0.0.1", s2.host
        finally:
            os.chdir(old)
            os.environ.pop("APP_HOST", None)
    print("selftest: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return _selftest()
    parser = argparse.ArgumentParser(prog="settings-app")
    parser.add_argument("command", choices=["show"])
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args(argv)
    if args.command == "show":
        settings = load_settings(
            {"host": args.host, "port": args.port},
            env_file=args.env_file,
        )
        print(json.dumps(settings.model_dump(), sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())