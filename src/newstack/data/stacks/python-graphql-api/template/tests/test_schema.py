"""Tests for the GraphQL schema."""

from __future__ import annotations

from graphql import graphql_sync

from {{ package_name }}.schema import schema


def test_hello_and_add() -> None:
    result = graphql_sync(schema, "{ hello add(a: 2, b: 3) }")
    assert result.errors is None
    assert result.data == {"hello": "world", "add": 5}


def test_variables() -> None:
    result = graphql_sync(
        schema, "query ($id: Int!) { user(id: $id) { id name } }", variable_values={"id": 7}
    )
    assert result.errors is None
    assert result.data == {"user": {"id": 7, "name": "user-7"}}


def test_aliases() -> None:
    result = graphql_sync(schema, "{ a: add(a: 1, b: 2) b: add(a: 10, b: 20) }")
    assert result.errors is None
    assert result.data == {"a": 3, "b": 30}


def test_resolver_error_has_path() -> None:
    result = graphql_sync(schema, "{ user(id: 0) { id name } }")
    assert result.data == {"user": None}
    assert result.errors is not None
    assert result.errors[0].path == ["user"]


def test_non_null_field_error() -> None:
    # `add` is non-null; forcing a null via a bad coercion surfaces as an error.
    result = graphql_sync(schema, "{ add(a: 1, b: null) }")
    assert result.errors is not None