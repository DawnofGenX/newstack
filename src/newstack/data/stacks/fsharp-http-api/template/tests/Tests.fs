module Textstat.Tests

// No test framework: one function that runs the checks, counts the failures and
// returns the exit code. The harness never touches a socket, so it is fast and
// the socket is proven separately by `newstack check`.

open System
open Textstat.Counts
open Textstat.Json
open Textstat.Contract

let mutable failures = 0

let private check (name: string) (ok: bool) =
    if ok then
        Console.WriteLine(sprintf "ok %s" name)
    else
        failures <- failures + 1
        Console.WriteLine(sprintf "FAIL %s" name)

let private encode (text: string) = Text.Encoding.UTF8.GetBytes text

let private json (body: byte[]) = Json.read body

let private statsLine (body: byte[]) =
    let counts = count body
    sprintf "%d/%d/%d" counts.Lines counts.Words counts.Bytes

let run () : int =
    failures <- 0

    check "an empty document has no counts" (statsLine [||] = "0/0/0")
    check "one line is one line" (statsLine (encode "hello world\n") = "1/2/12")
    check "a file without a newline still has no line" (statsLine (encode "a b") = "0/2/3")
    check "CRLF counts one line and two separators" (statsLine (encode "a\r\nb\r\n") = "2/2/6")
    check "utf8 is counted in bytes" (statsLine (encode "héllo wörld\n") = "1/2/14")
    check "tabs separate words" (statsLine (encode "a\tb") = "0/2/3")
    check "vertical tab is a separator" (statsLine (encode "a\vb") = "0/2/3")
    check "form feed is a separator" (statsLine (encode "a\fb") = "0/2/3")
    check "runs of separators are one gap" (statsLine (encode "  a  ") = "0/1/5")

    match json (encode "{\"text\":\"hi\"}") with
    | Text bytes -> check "a string body is text" (Text.Encoding.UTF8.GetString bytes = "hi")
    | _ -> check "a string body is text" false

    match json (encode "{\"text\":\"a\\nb\"}") with
    | Text bytes -> check "an escape becomes a newline" (statsLine bytes = "1/2/3")
    | _ -> check "an escape becomes a newline" false

    match json (encode "{\"text\":\"caf\\u00e9\"}") with
    | Text bytes -> check "a \\u escape is re-encoded as utf8" (statsLine bytes = "0/1/5")
    | _ -> check "a \\u escape is re-encoded as utf8" false

    match json (encode "{\"text\":\"\\ud83d\\ude00\"}") with
    | Text bytes -> check "a surrogate pair is one code point" (bytes.Length = 4)
    | _ -> check "a surrogate pair is one code point" false

    check "a missing member is missing text" (json (encode "{}") = MissingText)
    check "a number is not text" (json (encode "{\"text\":42}") = MissingText)
    check "the last text member wins" (json (encode "{\"text\":\"a\",\"text\":\"b\"}") = Text(encode "b"))
    check "a broken document is invalid" (json (encode "{") = Invalid)
    check "trailing garbage is invalid" (json (encode "{\"text\":\"a\"} x") = Invalid)
    check "an array is not a document" (json (encode "[]") = Invalid)
    check "nested objects are skipped" (json (encode "{\"meta\":{\"a\":[1,2]},\"text\":\"z\"}") = Text(encode "z"))

    check "a query parameter decodes" (queryText "/stats?text=hello%20world%0A" = Some(encode "hello world\n"))
    check "plus is a space" (queryText "/stats?text=a+b" = Some(encode "a b"))
    check "no query is no text" (queryText "/stats" = None)
    check "the first text wins" (queryText "/stats?text=a&text=b" = Some(encode "a"))
    check "other keys are ignored" (queryText "/stats?other=1" = None)

    let bodyOf (reply: Reply) = Text.Encoding.UTF8.GetString reply.Body
    check "health is ok" (bodyOf (route "GET" "/health" [||]) = "{\"status\":\"ok\"}")
    check "a GET stats counts the query" (bodyOf (route "GET" "/stats?text=a%20b%0A" [||]) = "{\"text\":\"a b\\n\",\"lines\":1,\"words\":2,\"bytes\":4}")
    check "a POST stats counts the body" (bodyOf (route "POST" "/stats" (encode "{\"text\":\"a b\\n\"}")) = "{\"text\":\"a b\\n\",\"lines\":1,\"words\":2,\"bytes\":4}")
    check "an empty body is invalid json" ((route "POST" "/stats" (encode "x")).Status = 422)
    check "missing text is 422" ((route "POST" "/stats" (encode "{}")).Status = 422)
    check "unknown route is 404" ((route "GET" "/nope" [||]).Status = 404)
    check "404 names the route" (bodyOf (route "GET" "/nope" [||]) = "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}")
    check "wrong method is 405" ((route "DELETE" "/health" [||]).Status = 405)
    check "a method on an unknown route is 404" ((route "DELETE" "/nope" [||]).Status = 404)

    if failures = 0 then
        Console.WriteLine "checks: all passed"
        0
    else
        Console.WriteLine(sprintf "failures: %d" failures)
        1
