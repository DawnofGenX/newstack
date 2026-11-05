import gleam/dynamic/decode
import gleam/http.{Get, Post}
import gleam/json
import gleam/list
import gleam/option
import gleam/result
import gleam/uri

import {{ package_name }}/count

pub type Reply {
  Reply(status: Int, body: String)
}

fn counts_json(text: String, counts: count.Counts) -> String {
  json.object([
    #("text", json.string(text)),
    #("lines", json.int(counts.lines)),
    #("words", json.int(counts.words)),
    #("bytes", json.int(counts.bytes)),
  ])
  |> json.to_string
}

fn pairstring(name: String, value: String) -> #(String, json.Json) {
  #(name, json.string(value))
}

fn error(status: Int, code: String, detail: option.Option(String)) -> Reply {
  let fields = case detail {
    option.Some(detail) -> [
      pairstring("error", code),
      pairstring("detail", detail),
    ]
    option.None -> [pairstring("error", code)]
  }
  Reply(status: status, body: json.object(fields) |> json.to_string)
}

fn text_param(query: String) -> option.Option(String) {
  case uri.parse_query(query) {
    Error(_) -> option.None
    Ok(params) ->
      params
      |> list.find(fn(pair) { pair.0 == "text" })
      |> result.map(fn(pair) { pair.1 })
      |> option.from_result
  }
}

fn text_body() -> decode.Decoder(String) {
  use text <- decode.field("text", decode.string)
  decode.success(text)
}

fn method_name(method: http.Method) -> String {
  case method {
    http.Get -> "GET"
    http.Post -> "POST"
    http.Patch -> "PATCH"
    http.Put -> "PUT"
    http.Delete -> "DELETE"
    http.Head -> "HEAD"
    http.Options -> "OPTIONS"
    http.Trace -> "TRACE"
    http.Connect -> "CONNECT"
    http.Other(other) -> other
  }
}

/// The whole HTTP contract is a pure function: `(method, path, query, body)` in,
/// a status and a JSON document out. That keeps it testable without a socket.
pub fn route(
  method: http.Method,
  path: String,
  query: String,
  body: String,
) -> Reply {
  case method, path {
    Get, "/health" -> Reply(status: 200, body: "{\"status\":\"ok\"}")
    Get, "/stats" ->
      case text_param(query) {
        option.Some(text) ->
          Reply(status: 200, body: counts_json(text, count.count_text(text)))
        option.None ->
          error(
            422,
            "missing_text",
            option.Some("the `text` query parameter is required"),
          )
      }
    Post, "/stats" ->
      case json.parse(from: body, using: text_body()) {
        Ok(text) ->
          Reply(status: 200, body: counts_json(text, count.count_text(text)))
        Error(_) ->
          case json.parse(from: body, using: decode.success(Nil)) {
            Ok(_) ->
              error(422, "missing_text", option.Some("`text` must be a string"))
            Error(_) ->
              error(
                422,
                "invalid_json",
                option.Some("the request body must be a JSON object"),
              )
          }
      }
    _, "/health" -> error(405, "method_not_allowed", option.None)
    _, "/stats" -> error(405, "method_not_allowed", option.None)
    _, _ ->
      error(
        404,
        "not_found",
        option.Some("no route for " <> method_name(method) <> " " <> path),
      )
  }
}
