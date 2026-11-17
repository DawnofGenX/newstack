"""Prometheus metrics for the exporter."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

app_up = Gauge("app_up", "Whether the exporter process is up.")
app_up.set(1)

requests_total = Counter(
    "app_requests_total",
    "Total HTTP requests handled.",
    ["endpoint"],
)


def render_metrics() -> bytes:
    return generate_latest()


def content_type() -> str:
    return CONTENT_TYPE_LATEST