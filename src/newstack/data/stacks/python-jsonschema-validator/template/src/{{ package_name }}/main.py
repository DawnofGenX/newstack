"""CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys

from .validator import load_json, render_report, validate_document


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()

    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="cmd", required=True)
    vp = sub.add_parser("validate")
    vp.add_argument("schema")
    vp.add_argument("document")
    vp.add_argument("--json", action="store_true", dest="as_json")
    ns = parser.parse_args(args)
    if ns.cmd != "validate":
        return 2
    try:
        schema = load_json(ns.schema)
        doc = load_json(ns.document)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = validate_document(doc, schema)
    if ns.as_json:
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    else:
        print(render_report(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())