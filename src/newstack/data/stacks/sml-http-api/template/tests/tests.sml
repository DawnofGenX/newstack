(* The gate: every contract answer, no socket, no port. *)
structure Tests = struct
  open Harness

  fun countOf text = Counts.count text
  fun contains (needle, hay) = String.isSubstring needle hay

  fun eq (name, got, want) = check (name ^ " (" ^ got ^ ")", got = want)
  fun eqInt (name, got, want) = eq (name, Int.toString got, Int.toString want)

  fun routeOf {method, path, query, body} =
      Contract.route {method = method, path = path, query = query, body = body}

  fun stats text =
      "{\"text\":" ^ Contract.jsonQuote text
      ^ ",\"lines\":" ^ Int.toString (#lines (Counts.count text))
      ^ ",\"words\":" ^ Int.toString (#words (Counts.count text))
      ^ ",\"bytes\":" ^ Int.toString (#bytes (Counts.count text)) ^ "}"

  fun run () =
      let
        (* counting *)
        val hello = countOf "hello world\n"
        val () = eqInt ("one newline is one line", #lines hello, 1)
        val () = eqInt ("two words", #words hello, 2)
        val () = eqInt ("twelve bytes", #bytes hello, 12)

        val utf8 = countOf "h\195\169llo w\195\182rld\n"
        val () = eqInt ("utf8 lines", #lines utf8, 1)
        val () = eqInt ("utf8 words", #words utf8, 2)
        val () = eqInt ("utf8 bytes count the encoding", #bytes utf8, 14)

        val empty = countOf ""
        val () = eqInt ("empty lines", #lines empty, 0)
        val () = eqInt ("empty words", #words empty, 0)
        val () = eqInt ("empty bytes", #bytes empty, 0)

        val two = countOf "a b\nc\n"
        val () = eqInt ("two lines", #lines two, 2)
        val () = eqInt ("three words", #words two, 3)
        val () = eqInt ("six bytes", #bytes two, 6)

        val bare = countOf "a b"
        val () = eqInt ("no newline is no line", #lines bare, 0)
        val () = eqInt ("two words with no newline", #words bare, 2)

        val odd = countOf "a\011b\012c\n"
        val () = eqInt ("vertical tab and form feed separate words", #words odd, 3)

        val spaced = countOf "a   b\r\n"
        val () = eqInt ("a run of spaces is one separator", #words spaced, 2)
        val () = eqInt ("carriage return is not a line", #lines spaced, 1)

        (* json reader *)
        val () = check ("a string body is text",
                        case Json.readBody "{\"text\": \"hi\"}" of Json.Text s => s = "hi" | _ => false)
        val () = check ("the last key wins",
                        case Json.readBody "{\"text\": \"a\", \"text\": \"b\"}" of
                            Json.Text s => s = "b" | _ => false)
        val () = check ("a number is not a string",
                        case Json.readBody "{\"text\": 42}" of Json.Missing => true | _ => false)
        val () = check ("no text key is missing",
                        case Json.readBody "{\"other\": \"x\"}" of Json.Missing => true | _ => false)
        val () = check ("a null text is not a string",
                        case Json.readBody "{\"text\": null}" of Json.Missing => true | _ => false)
        val () = check ("an array body is invalid",
                        case Json.readBody "[1, 2]" of Json.Invalid => true | _ => false)
        val () = check ("plain text is invalid",
                        case Json.readBody "nope" of Json.Invalid => true | _ => false)
        val () = check ("trailing data is invalid",
                        case Json.readBody "{\"text\": \"x\"} extra" of Json.Invalid => true | _ => false)
        val () = check ("an unterminated object is invalid",
                        case Json.readBody "{\"text\": \"x\"" of Json.Invalid => true | _ => false)
        val () = check ("escapes are decoded",
                        case Json.readBody "{\"text\": \"a\\nb\\tc\\\"d\\\\e\\/f\"}" of
                            Json.Text s => s = "a\nb\tc\"d\\e/f" | _ => false)
        val () = check ("a \\u escape becomes utf-8",
                        case Json.readBody "{\"text\": \"\\u00e9\"}" of
                            Json.Text s => String.size s = 2
                                           andalso ord (String.sub (s, 0)) = 195
                                           andalso ord (String.sub (s, 1)) = 169
                          | _ => false)
        val () = check ("a surrogate pair becomes four bytes",
                        case Json.readBody "{\"text\": \"\\ud83d\\ude42\"}" of
                            Json.Text s => String.size s = 4 | _ => false)
        val () = check ("nested values are accepted",
                        case Json.readBody "{\"note\": {\"a\": [1, true, null]}, \"text\": \"ok\"}" of
                            Json.Text s => s = "ok" | _ => false)

        (* contract *)
        val health = routeOf {method = "GET", path = "/health", query = "", body = ""}
        val () = eq ("health status", Int.toString (#status health), "200")
        val () = eq ("health body", #body health, "{\"status\":\"ok\"}")

        val get = routeOf {method = "GET", path = "/stats", query = "?text=hello%20world%0A", body = ""}
        val () = eqInt ("get status", #status get, 200)
        val () = eq ("get body", #body get, stats "hello world\n")

        val plus = routeOf {method = "GET", path = "/stats", query = "?text=a+b", body = ""}
        val () = eq ("plus is a space", #body plus, stats "a b")

        val accented = routeOf {method = "GET", path = "/stats", query = "?text=h%C3%A9llo", body = ""}
        val () = check ("percent escapes decode to utf-8",
                        contains ("\"text\":\"h\195\169llo\"", #body accented))

        val first = routeOf {method = "GET", path = "/stats", query = "?text=one&text=two", body = ""}
        val () = eq ("the first query value wins", #body first, stats "one")

        val absent = routeOf {method = "GET", path = "/stats", query = "", body = ""}
        val () = eqInt ("no text is 422", #status absent, 422)
        val () = eq ("no text body", #body absent, "{\"error\":\"missing_text\"}")

        val posted = routeOf {method = "POST", path = "/stats", query = "",
                             body = "{\"text\": \"a b\\nc\\n\"}"}
        val () = eqInt ("post status", #status posted, 200)
        val () = eq ("post body", #body posted, stats "a b\nc\n")

        val number = routeOf {method = "POST", path = "/stats", query = "", body = "{\"text\": 42}"}
        val () = eqInt ("a number is 422", #status number, 422)
        val () = eq ("a number is missing_text", #body number, "{\"error\":\"missing_text\"}")

        val broken = routeOf {method = "POST", path = "/stats", query = "", body = "nope"}
        val () = eqInt ("broken json is 422", #status broken, 422)
        val () = eq ("broken json body", #body broken, "{\"error\":\"invalid_json\"}")

        val wrong = routeOf {method = "DELETE", path = "/health", query = "", body = ""}
        val () = eqInt ("wrong method is 405", #status wrong, 405)
        val () = eq ("405 body", #body wrong, "{\"error\":\"method_not_allowed\"}")

        val gone = routeOf {method = "GET", path = "/nope", query = "", body = ""}
        val () = eqInt ("unknown path is 404", #status gone, 404)
        val () = eq ("404 detail", #body gone,
                     "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}")

        val quoted = Contract.jsonQuote "a\"b\\c\nd\te"
        val () = eq ("json quote escapes", quoted, "\"a\\\"b\\\\c\\nd\\te\"")

        val control = Contract.jsonQuote "\001"
        val () = eq ("a control byte is escaped", control, "\"\\u0001\"")
      in
        report ()
      end
end
