"""Offline contract check: `python -m {{ package_name }} --selftest`."""

from __future__ import annotations

from graphql import graphql_sync

from .schema import schema


def run() -> int:
    result = graphql_sync(schema, "{ hello add(a: 2, b: 3) }")
    assert result.errors is None or not result.errors
    assert result.data == {"hello": "world", "add": 5}

    aliased = graphql_sync(schema, "{ a: add(a: 1, b: 2) b: add(a: 10, b: 20) }")
    assert aliased.data == {"a": 3, "b": 30}

    vars_result = graphql_sync(
        schema, "query ($id: Int!) { user(id: $id) { id name } }", variable_values={"id": 7}
    )
    assert vars_result.data == {"user": {"id": 7, "name": "user-7"}}

    err = graphql_sync(schema, "{ user(id: 0) { id name } }")
    assert err.data is not None
    assert err.data["user"] is None
    assert err.errors and err.errors[0].path == ["user"]
    print("selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())