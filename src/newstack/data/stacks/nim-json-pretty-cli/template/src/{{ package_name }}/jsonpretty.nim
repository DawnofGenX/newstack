## JSON pretty printing with sorted keys.

import std/[json, algorithm]

proc sortNode*(node: JsonNode): JsonNode =
  ## Returns a copy of `node` with object keys sorted recursively.
  case node.kind
  of JObject:
    result = newJObject()
    var keys: seq[string] = @[]
    for key, _ in node:
      keys.add(key)
    keys.sort()
    for k in keys:
      result[k] = sortNode(node[k])
  of JArray:
    result = newJArray()
    for item in node:
      result.add(sortNode(item))
  else:
    result = node

proc prettyJson*(text: string, indent: int = 2, sortKeys: bool = true,
                compact: bool = false): string =
  ## Parses `text` and renders it. Raises `JsonParsingError` on bad input.
  let parsed = parseJson(text)
  let node = if sortKeys: sortNode(parsed) else: parsed
  if compact:
    result = $node
  else:
    result = pretty(node, indent)