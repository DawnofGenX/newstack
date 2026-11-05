import std/[json, unittest]

import ../src/app, ../src/counts

suite "countText":
  test "counts lines, words and bytes":
    let counts = countText("hello world\n")
    check counts.lines == 1
    check counts.words == 2
    check counts.bytes == 12

  test "an empty string is all zeroes":
    let counts = countText("")
    check counts.lines == 0
    check counts.words == 0
    check counts.bytes == 0

  test "blank lines are lines without words":
    let counts = countText("\n\nx\n")
    check counts.lines == 3
    check counts.words == 1
    check counts.bytes == 4

  test "whitespace that is not a newline still counts as bytes":
    let counts = countText("  \t ")
    check counts.lines == 0
    check counts.words == 0
    check counts.bytes == 4

  test "bytes follow UTF-8, not characters":
    let counts = countText("héllo wörld\n")
    check counts.lines == 1
    check counts.words == 2
    check counts.bytes == 14

  test "astral characters are four bytes":
    let counts = countText("🙂\n")
    check counts.lines == 1
    check counts.words == 1
    check counts.bytes == 5

  test "a trailing run without a newline is one word":
    let counts = countText("abc")
    check counts.lines == 0
    check counts.words == 1
    check counts.bytes == 3

suite "route":
  test "health answers 200 and ok":
    let reply = route("GET", "/health", "", "")
    check reply.status == 200
    check $reply.body == """{"status":"ok"}"""

  test "stats reads the query parameter":
    let reply = route("GET", "/stats", "text=hello%20world%0A", "")
    check reply.status == 200
    let body = reply.body
    check body["text"].getStr() == "hello world\n"
    check body["lines"].getInt() == 1
    check body["words"].getInt() == 2
    check body["bytes"].getInt() == 12

  test "stats without a query parameter is a 422":
    let reply = route("GET", "/stats", "", "")
    check reply.status == 422
    check reply.body["error"].getStr() == "missing_text"

  test "post counts the JSON body":
    let reply = route("POST", "/stats", "", """{"text":"a b\nc\n"}""")
    check reply.status == 200
    check reply.body["lines"].getInt() == 2
    check reply.body["words"].getInt() == 3
    check reply.body["bytes"].getInt() == 6

  test "post keeps padding exactly as sent":
    let reply = route("POST", "/stats", "", """{"text":"  padded  \n"}""")
    check reply.status == 200
    check reply.body["lines"].getInt() == 1
    check reply.body["words"].getInt() == 1
    check reply.body["bytes"].getInt() == 11

  test "post without text is a 422":
    let reply = route("POST", "/stats", "", "{}")
    check reply.status == 422
    check reply.body["error"].getStr() == "missing_text"

  test "post with a non-string text is a 422":
    let reply = route("POST", "/stats", "", """{"text":42}""")
    check reply.status == 422
    check reply.body["error"].getStr() == "missing_text"

  test "post with a broken body is a 422":
    let reply = route("POST", "/stats", "", "not json")
    check reply.status == 422
    check reply.body["error"].getStr() == "invalid_json"

  test "an unknown route is a 404":
    let reply = route("GET", "/nope", "", "")
    check reply.status == 404
    check reply.body["error"].getStr() == "not_found"
    check reply.body["detail"].getStr() == "no route for GET /nope"

  test "an unsupported method on stats is a 405":
    let reply = route("DELETE", "/stats", "", "")
    check reply.status == 405
    check reply.body["error"].getStr() == "method_not_allowed"
