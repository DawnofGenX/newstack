describe("textstat_route health", function() {
  it("answers GET /health", function() {
    reply <- textstat_route("GET", "/health")
    expect_equal(reply$status, 200L, "health is a 200")
    expect_equal(reply$body, list(status = "ok"), "health body is a status object")
  })
})

describe("textstat_route GET /stats", function() {
  it("counts the query parameter", function() {
    reply <- textstat_route("GET", "/stats", "text=hello%20world%0A")
    expect_equal(reply$status, 200L, "a text in the query string is a 200")
    expect_equal(reply$body$text, "hello world\n", "percent escapes are decoded")
    expect_equal(reply$body$lines, 1L, "one line")
    expect_equal(reply$body$words, 2L, "two words")
    expect_equal(reply$body$bytes, 12L, "twelve bytes")
  })

  it("distinguishes a missing parameter from an empty one", function() {
    missing <- textstat_route("GET", "/stats")
    expect_equal(missing$status, 422L, "no text parameter is a 422")
    expect_equal(missing$body$error, "missing_text", "with a machine readable code")

    empty <- textstat_route("GET", "/stats", "text=")
    expect_equal(empty$status, 200L, "an empty text is still a text")
    expect_equal(empty$body$bytes, 0L, "and it counts zero bytes")
  })

  it("keeps the padding of the text it is given", function() {
    reply <- textstat_route("GET", "/stats", "text=%20%20padded%20%20%0A")
    expect_equal(reply$body$bytes, 11L, "padding is part of the answer")
    expect_equal(reply$body$words, 1L, "surrounding whitespace is not a word")
  })
})

describe("textstat_route POST /stats", function() {
  it("counts a JSON body", function() {
    reply <- textstat_route("POST", "/stats", NULL, "{\"text\":\"a b\\nc\\n\"}")
    expect_equal(reply$status, 200L, "a JSON body is a 200")
    expect_equal(reply$body$lines, 2L, "two lines")
    expect_equal(reply$body$words, 3L, "three words")
    expect_equal(reply$body$bytes, 6L, "six bytes")
  })

  it("rejects a body that is not JSON", function() {
    reply <- textstat_route("POST", "/stats", NULL, "nope")
    expect_equal(reply$status, 422L, "a broken body is a 422")
    expect_equal(reply$body$error, "invalid_json", "with an invalid_json code")
  })

  it("rejects a text that is not a string", function() {
    reply <- textstat_route("POST", "/stats", NULL, "{\"text\":42}")
    expect_equal(reply$status, 422L, "a number is not a text")
    expect_equal(reply$body$error, "missing_text", "with a missing_text code")

    empty_object <- textstat_route("POST", "/stats", NULL, "{}")
    expect_equal(empty_object$status, 422L, "an empty object has no text either")
  })
})

describe("textstat_route the rest", function() {
  it("answers 405 for a known path with the wrong method", function() {
    reply <- textstat_route("DELETE", "/health")
    expect_equal(reply$status, 405L, "the path exists, the method does not")
    expect_equal(reply$body$error, "method_not_allowed", "with a 405 code")
  })

  it("answers 404 for an unknown path", function() {
    reply <- textstat_route("GET", "/nope")
    expect_equal(reply$status, 404L, "an unknown path is a 404")
    expect_equal(reply$body$error, "not_found", "with a not_found code")
    expect_equal(
      reply$body$detail,
      "no route for GET /nope",
      "and it names what was asked for"
    )
  })
})

describe("textstat_query_param", function() {
  it("decodes escapes and keeps values that contain an equals sign", function() {
    expect_equal(
      textstat_query_param("a=1&text=x%3Dy", "text"),
      "x=y",
      "a value may contain an encoded equals sign"
    )
    expect_equal(
      textstat_query_param("a=1", "text"),
      NULL,
      "an absent parameter is NULL, not an empty string"
    )
    expect_equal(
      textstat_query_param("", "text"),
      NULL,
      "an empty query string has no parameters"
    )
    expect_equal(
      textstat_query_param("?text=abc%0A", "text"),
      "abc\n",
      "plumber hands over the query string with its question mark"
    )
  })
})
