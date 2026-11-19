val () =
  let
    val j = Json.parse "{\"b\":2,\"a\":[1,2,3]}"
    val out = Json.pretty j
    val expected = "{\n  \"a\": [\n    1,\n    2,\n    3\n  ],\n  \"b\": 2\n}"
  in
    Harness.equal ("sorted pretty", out, expected);
    Harness.check ("parse error raised", (Json.parse "{bad" handle Json.Parse _ => Json.JNull) = Json.JNull);
    Harness.finish ()
  end
