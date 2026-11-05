"""Litestar glue: everything this file does is hand a request to `contract.route`.

The handler is deliberately untyped — no `text: str` parameter, no `Body[dict]`.
Litestar validates declared parameters before the handler runs and answers `400`
with its own error envelope, which would turn `missing_text` into "Expected
`str`, got `NoneType`" and make the contract untestable. Reading `Request`
directly keeps every status code a decision this project makes.

Two other Litestar behaviours are worth knowing, both why the code below looks
the way it does:

* `raw_path` is the path *as sent*, still percent-encoded. `request.url.path`
  arrives decoded and re-quoted, so `/stats?text=%2B` would round-trip to `%2B`
  or `+` depending on the code path — the 404 detail prints what the client sent.
* Litestar answers `HEAD` for a `GET` route itself, with the GET body's length
  and no body. The catch-all claims every method, so `HEAD /health` reaches the
  contract and gets the same `405` every other stack in this family returns.
"""

from __future__ import annotations

from litestar import Litestar, Request, Response, route

from .contract import route as plan

JSON = "application/json"

#: every method a client could send; the contract decides which are allowed
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"]


def target_of(request: Request) -> str:
    """The request target exactly as the client sent it, query string included.

    Litestar's `raw_path` already carries `?query`: appending `query_string` as
    well duplicates it, and `GET /stats?text=a+b` then counts `"a b?text=a b"`.
    The fallback keeps the adapter honest on a scope that splits them.
    """
    raw_path = request.scope.get("raw_path") or b"/"
    query = request.scope.get("query_string") or b""
    path = raw_path.decode("latin-1")
    if query and "?" not in path:
        return path + "?" + query.decode("latin-1")
    return path


@route("/{path:path}", http_method=METHODS, status_code=200)
async def catch_all(request: Request) -> Response[str]:
    status, body = plan(request.method, target_of(request), await request.body())
    return Response(content=body, status_code=status, media_type=JSON)


@route("/", http_method=METHODS, status_code=200)
async def root(request: Request) -> Response[str]:
    status, body = plan(request.method, target_of(request), await request.body())
    return Response(content=body, status_code=status, media_type=JSON)


def create_app() -> Litestar:
    return Litestar(
        [root, catch_all],
        # Litestar's own 404/405 handlers would win over the catch-all's body
        # shape for anything the router rejects before dispatch; the router only
        # rejects malformed targets here, so the default handlers stay, with the
        # same three fields the contract prints.
        openapi_config=None,
        debug=False,
    )


app = create_app()
