"""GraphQL schema: a query with arguments, resolver errors with paths."""

from __future__ import annotations

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInt,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)


def _resolve_user(_root, _info, id: int) -> dict:
    if id <= 0:
        raise ValueError(f"unknown user {id}")
    return {"id": id, "name": f"user-{id}"}


def _resolve_add(_root, _info, a: int, b: int) -> int:
    return a + b


UserType = GraphQLObjectType(
    "User",
    {
        "id": GraphQLField(GraphQLNonNull(GraphQLInt)),
        "name": GraphQLField(GraphQLNonNull(GraphQLString)),
    },
)

QueryType = GraphQLObjectType(
    "Query",
    {
        "hello": GraphQLField(GraphQLString, resolve=lambda _r, _i: "world"),
        "add": GraphQLField(
            GraphQLNonNull(GraphQLInt),
            args={
                "a": GraphQLArgument(GraphQLNonNull(GraphQLInt)),
                "b": GraphQLArgument(GraphQLNonNull(GraphQLInt)),
            },
            resolve=_resolve_add,
        ),
        "user": GraphQLField(
            UserType,
            args={"id": GraphQLArgument(GraphQLNonNull(GraphQLInt))},
            resolve=_resolve_user,
        ),
    },
)

schema = GraphQLSchema(query=QueryType)