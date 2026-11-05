"""A deliberately dim OpenAI-compatible server, so tests need no network.

Prompts containing FAIL400 answer 400 forever; FAIL429 answers 429 the first
`flaky_after` times per prompt and then succeeds, which is what proves the
retry path instead of asserting it.
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class State:
    """Attempt counters, keyed by prompt."""

    def __init__(self) -> None:
        self.attempts: dict[str, int] = {}

    def count(self, prompt: str) -> int:
        """Count one attempt at `prompt` and return the new total."""
        self.attempts[prompt] = self.attempts.get(prompt, 0) + 1
        return self.attempts[prompt]


def make_handler(state: State, *, flaky_after: int = 2) -> type[BaseHTTPRequestHandler]:
    """Build a handler class bound to `state`."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args: object) -> None:
            """Keep the test output clean."""

        def do_POST(self) -> None:  # http.server's spelling
            length = int(self.headers.get("content-length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"error": {"message": "not json"}})
                return
            prompt = body.get("messages", [{}])[-1].get("content", "")
            if "FAIL400" in prompt:
                self._send(400, {"error": {"message": "bad request"}})
                return
            if "FAIL429" in prompt and state.count(prompt) <= flaky_after:
                self._send(429, {"error": {"message": "slow down"}})
                return
            self._send(
                200,
                {
                    "model": body.get("model", "stub-model"),
                    "choices": [{"message": {"role": "assistant", "content": f"echo: {prompt}"}}],
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": 1,
                    },
                },
            )

        def _send(self, status: int, payload: dict) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    return Handler


def serve(port: int = 0, *, flaky_after: int = 2) -> tuple[ThreadingHTTPServer, State]:
    """Start the stub on `port` (0 picks a free one) and return it running."""
    state = State()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(state, flaky_after=flaky_after))
    threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
    ).start()
    return server, state


def main(argv: list[str] | None = None) -> int:
    """Run the stub in the foreground, printing the port it bound."""
    parser = argparse.ArgumentParser(description="OpenAI-compatible stub server")
    parser.add_argument("--port", type=int, default=5468)
    parser.add_argument("--flaky-after", type=int, default=2)
    args = parser.parse_args(argv)
    server, _state = serve(args.port, flaky_after=args.flaky_after)
    print(f"stub listening on 127.0.0.1:{server.server_address[1]}", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
