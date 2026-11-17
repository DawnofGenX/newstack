"""JWT helpers: load users from env, issue and verify HS256 tokens."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import jwt

DEFAULT_SECRET = "dev-secret-change-me"
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 300


def secret() -> str:
    return os.environ.get("JWT_SECRET") or DEFAULT_SECRET


def load_users() -> dict[str, str]:
    raw = os.environ.get("AUTH_USERS")
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    return {"alice": "wonderland", "bob": "builder"}


def issue_token(username: str) -> str:
    now = int(time.time())
    claims = {
        "sub": username,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    return jwt.encode(claims, secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, secret(), algorithms=[ALGORITHM])