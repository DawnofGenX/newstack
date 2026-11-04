"""Unit tests: no server, no Docker, no network."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from service import SERVICE_NAME, State, build_reply  # noqa: E402


class HealthTest(unittest.TestCase):
    def test_health_is_ok_json(self) -> None:
        reply = build_reply("/health", State())
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply.content_type, "application/json")
        body = json.loads(reply.body)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], SERVICE_NAME)

    def test_health_ignores_a_query_string(self) -> None:
        self.assertEqual(build_reply("/health?probe=1", State()).status, 200)

    def test_health_ignores_a_trailing_slash(self) -> None:
        self.assertEqual(build_reply("/health/", State()).status, 200)


class MetricsTest(unittest.TestCase):
    def test_metrics_counts_requests(self) -> None:
        state = State()
        build_reply("/", state)
        build_reply("/health", state)
        body = build_reply("/metrics", state).body
        self.assertIn("requests_total 3", body)
        self.assertIn("# TYPE uptime_seconds gauge", body)

    def test_metrics_is_plain_text(self) -> None:
        self.assertTrue(build_reply("/metrics", State()).content_type.startswith("text/plain"))


class RootTest(unittest.TestCase):
    def test_root_lists_endpoints(self) -> None:
        body = json.loads(build_reply("/", State()).body)
        self.assertEqual(body["endpoints"], ["/", "/health", "/metrics"])

    def test_unknown_path_is_404_and_names_the_path(self) -> None:
        reply = build_reply("/nope", State())
        self.assertEqual(reply.status, 404)
        self.assertEqual(json.loads(reply.body)["path"], "/nope")

    def test_post_is_405(self) -> None:
        self.assertEqual(build_reply("/health", State(), method="POST").status, 405)


if __name__ == "__main__":
    unittest.main()
