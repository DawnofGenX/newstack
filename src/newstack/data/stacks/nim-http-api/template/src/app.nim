## The HTTP contract, expressed as a pure function.
##
## ``route`` takes a method, a path, the raw query string and the raw body and
## returns the status and the JSON document — no sockets, so the whole contract
## is testable with ``nimble test``. The server in `server.nim` adapts a real
## request to it.

import std/[json, strutils, uri]

import ./counts

type
  Reply* = object
    status*: int
    body*: JsonNode

proc reply(status: int, body: JsonNode): Reply =
  Reply(status: status, body: body)

proc errorReply(status: int, code: string, detail: string = ""): Reply =
  var body = %*{"error": code}
  if detail.len > 0:
    body["detail"] = %detail
  reply(status, body)

proc parseObject(text: string): JsonNode =
  ## Returns nil when `text` is not a JSON object, so callers answer 422
  ## instead of crashing the server.
  try:
    let parsed = parseJson(text)
    if parsed.kind == JObject: parsed else: nil
  except CatchableError:
    nil

proc queryPairs(query: string): seq[(string, string)] =
  ## `text=a%20b&x=1` → @[("a b", …)] — values are percent-decoded and `+` is
  ## a space, exactly like a browser sends them.
  for pair in query.split('&'):
    if pair.len == 0:
      continue
    let separator = pair.find('=')
    if separator < 0:
      result.add((decodeUrl(pair), ""))
    else:
      result.add((decodeUrl(pair[0 ..< separator]), decodeUrl(pair[separator + 1 ..^ 1])))

proc route*(httpMethod, path, query, body: string): Reply =
  ## The whole service contract in one pure function.
  if path == "/health":
    if httpMethod != "GET":
      return errorReply(405, "method_not_allowed")
    return reply(200, %*{"status": "ok"})
  if path == "/stats":
    if httpMethod == "GET":
      for (key, value) in queryPairs(query):
        if key == "text":
          return reply(200, countsJson(value, countText(value)))
      return errorReply(422, "missing_text", "the `text` query parameter is required")
    if httpMethod == "POST":
      let payload = parseObject(body)
      if payload.isNil:
        return errorReply(422, "invalid_json", "the request body must be a JSON object")
      let node = payload{"text"}
      if node.isNil or node.kind != JString:
        return errorReply(422, "missing_text", "`text` must be a string")
      let text = node.getStr()
      return reply(200, countsJson(text, countText(text)))
    return errorReply(405, "method_not_allowed")
  errorReply(404, "not_found", "no route for " & httpMethod & " " & path)
