"""Saying what happened, in the words that would have saved the caller a debug."""

from __future__ import annotations

from .router import MATCH, NOT_ALLOWED, Resolution, Route, Router


def resolution_lines(resolution: Resolution) -> list[str]:
    lines = [f"method     {resolution.method}", f"path       {resolution.path}"]
    if resolution.kind == MATCH:
        route = resolution.route
        assert route is not None
        lines.append("verdict    matched")
        lines.append(f"route      {route.text}")
        if route.name:
            lines.append(f"name       {route.name}")
        if resolution.params:
            for name, value in resolution.params:
                lines.append(f"param      {name} = {value!r}")
        else:
            lines.append("param      (none)")
        return lines
    if resolution.kind == NOT_ALLOWED:
        lines.append("verdict    wrong method")
        lines.append(f"allow      {', '.join(resolution.allow)}")
        lines.append(f"reason     {resolution.reason}")
        return lines
    lines.append("verdict    no route")
    lines.append(f"reason     {resolution.reason}")
    return lines


def table_lines(routes: list[Route]) -> list[str]:
    lines = [f"{len(routes)} route(s)"]
    width = max((len(route.pattern.text) for route in routes), default=10)
    for route in routes:
        lines.append(f"  {route.method:<7} {route.pattern.text:<{width}}  {route.pattern.shape()}")
    return lines


def nearest_hint(router: Router, path: str) -> str:
    """Name the closest registered shape, so a typo has somewhere to look."""
    from .pattern import split_path

    try:
        segments = split_path(path)
    except Exception:
        return ""
    best = ""
    for route in router.routes:
        if len(route.pattern.segments) != len(segments):
            continue
        same = sum(
            1
            for index, piece in enumerate(route.pattern.segments)
            if piece.kind == "static" and piece.text == segments[index]
        )
        if same:
            candidate = f"{route.text} shares {same} segment(s) with this path"
            if not best or same > int(best.split("shares ")[1].split()[0]):
                best = candidate
    return best
