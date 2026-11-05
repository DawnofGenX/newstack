## The socket layer: adapt `asynchttpserver` requests to `app.route`.

import std/[asynchttpserver, asyncdispatch, json, strutils, uri]

import ./app

proc handleRequest*(req: Request): Future[void] {.async.} =
  let body = req.body
  let reply = route(
    httpMethod = $req.reqMethod,
    path = req.url.path,
    query = req.url.query,
    body = body,
  )
  await req.respond(
    code = HttpCode(reply.status),
    content = $reply.body & "\n",
    headers = newHttpHeaders({"Content-Type": "application/json"}),
  )

proc start*(port: int) {.async.} =
  var server = newAsyncHttpServer()
  echo "listening on http://127.0.0.1:", port
  await server.serve(Port(port), handleRequest)
