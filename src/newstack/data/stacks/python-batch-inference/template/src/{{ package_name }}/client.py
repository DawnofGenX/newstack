"""A small client for any OpenAI-compatible chat endpoint.

Standard library only, so the tool has no dependency tree to negotiate and the
tests can point it at an in-process stub.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable

RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504})


class RequestFailed(RuntimeError):
    """One request could not be completed; the run records it and continues."""


class ChatClient:
    """POST /chat/completions with bounded retries and exponential back-off."""

    def __init__(
        self,
        base_url: str,
        *,
        model: str = "stub-model",
        timeout: float = 10.0,
        max_attempts: int = 4,
        backoff: float = 0.05,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff = backoff
        self._sleep = sleep

    def payload(self, prompt: str) -> bytes:
        """Build the request body, so a test can assert on it without a socket."""
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        return json.dumps(body).encode("utf-8")

    def _once(self, prompt: str) -> tuple[str, int, int]:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=self.payload(prompt),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        output = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage") or {}
        return output, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))

    def complete(self, prompt: str) -> tuple[str, int, int, int]:
        """Return ``(output, tokens_in, tokens_out, attempts)`` or raise RequestFailed.

        A 4xx that is not 408/429 is permanent: retrying a malformed request only
        wastes the caller's quota, so it fails on the first attempt.
        """
        last = "no attempt made"
        for attempt in range(1, self.max_attempts + 1):
            try:
                output, tokens_in, tokens_out = self._once(prompt)
                return output, tokens_in, tokens_out, attempt
            except urllib.error.HTTPError as exc:
                last = f"http {exc.code}"
                if exc.code not in RETRY_STATUS:
                    raise RequestFailed(last) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last = f"network {exc}"
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise RequestFailed(f"bad response: {exc}") from exc
            if attempt < self.max_attempts:
                self._sleep(self.backoff * 2 ** (attempt - 1))
        raise RequestFailed(f"gave up after {self.max_attempts} attempts ({last})")
