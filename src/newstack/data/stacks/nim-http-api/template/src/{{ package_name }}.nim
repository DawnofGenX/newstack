## Entry point: read PORT and serve the counting API.

import std/[asyncdispatch, os, strutils]

import ./server

proc main() =
  var port = 8080
  let configured = getEnv("PORT")
  if configured.len > 0:
    port = parseInt(configured)
  waitFor start(port)

when isMainModule:
  main()
