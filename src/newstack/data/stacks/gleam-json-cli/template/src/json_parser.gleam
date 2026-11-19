// GLEAM_JSON_CLI_MARKER_9f3a1c
import gleam/list
import gleam/string

pub type Json {
  JNull
  JBool(Bool)
  JNum(String)
  JStr(String)
  JArr(List(Json))
  JObj(List(#(String, Json)))
}

pub type ParseError {
  ParseError(msg: String, pos: Int)
}

// ---------- parser ----------

type P {
  P(input: String, pos: Int)
}

fn at(p: P, i: Int) -> String {
  case i >= string.length(p.input) {
    True -> ""
    False -> string.slice(p.input, i, 1)
  }
}

fn cur(p: P) -> String { at(p, p.pos) }

fn advance(p: P, n: Int) -> P { P(p.input, p.pos + n) }

fn skip_ws(p: P) -> P {
  case cur(p) {
    " " | "\t" | "\n" | "\r" -> skip_ws(advance(p, 1))
    _ -> p
  }
}

fn parse(p: P) -> Result(#(Json, P), ParseError) {
  let p = skip_ws(p)
  parse_value(p)
}

fn parse_value(p: P) -> Result(#(Json, P), ParseError) {
  case cur(p) {
    "{" -> parse_obj(p)
    "[" -> parse_arr(p)
    "\"" -> {
      case parse_str(p) {
        Ok(#(s, p2)) -> Ok(#(JStr(s), p2))
        Error(e) -> Error(e)
      }
    }
    "t" -> parse_literal(p, "true", JBool(True))
    "f" -> parse_literal(p, "false", JBool(False))
    "n" -> parse_literal(p, "null", JNull)
    _ -> parse_num(p)
  }
}

fn parse_literal(p: P, word: String, val: Json) -> Result(#(Json, P), ParseError) {
  let wlen = string.length(word)
  let chunk = string.slice(p.input, p.pos, wlen)
  case chunk == word {
    True -> Ok(#(val, advance(p, wlen)))
    False -> Error(ParseError("expected " <> word, p.pos))
  }
}

fn parse_str(p: P) -> Result(#(String, P), ParseError) {
  // assumes cur == "
  let p = advance(p, 1)
  parse_str_acc(p, "")
}

fn parse_str_acc(p: P, acc: String) -> Result(#(String, P), ParseError) {
  case cur(p) {
    "" -> Error(ParseError("unterminated string", p.pos))
    "\"" -> Ok(#(acc, advance(p, 1)))
    "\\" -> {
      let c = at(p, p.pos + 1)
      case c {
        "\"" -> parse_str_acc(advance(p, 2), acc <> "\"")
        "\\" -> parse_str_acc(advance(p, 2), acc <> "\\")
        "/" -> parse_str_acc(advance(p, 2), acc <> "/")
        "n" -> parse_str_acc(advance(p, 2), acc <> "\n")
        "t" -> parse_str_acc(advance(p, 2), acc <> "\t")
        "r" -> parse_str_acc(advance(p, 2), acc <> "\r")
        "b" -> parse_str_acc(advance(p, 2), acc <> "\u{0008}")
        "f" -> parse_str_acc(advance(p, 2), acc <> "\u{000C}")
        "u" -> {
          // skip 4 hex digits, append replacement char placeholder
          let hex = string.slice(p.input, p.pos + 2, 4)
          parse_str_acc(advance(p, 6), acc <> "\\u" <> hex)
        }
        _ -> Error(ParseError("bad escape", p.pos))
      }
    }
    _ -> parse_str_acc(advance(p, 1), acc <> cur(p))
  }
}

fn parse_num(p: P) -> Result(#(Json, P), ParseError) {
  // read until delimiter
  let start = p.pos
  let p2 = read_num_chars(p)
  let raw = string.slice(p.input, start, p2.pos - start)
  case raw {
    "" -> Error(ParseError("expected value", p.pos))
    _ -> Ok(#(JNum(raw), p2))
  }
}

fn read_num_chars(p: P) -> P {
  case cur(p) {
    "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "-" | "+" | "." | "e" | "E" ->
      read_num_chars(advance(p, 1))
    _ -> p
  }
}

fn parse_arr(p: P) -> Result(#(Json, P), ParseError) {
  // cur == [
  let p = advance(p, 1)
  let p = skip_ws(p)
  case cur(p) {
    "]" -> Ok(#(JArr([]), advance(p, 1)))
    _ -> parse_arr_items(p, [])
  }
}

fn parse_arr_items(p: P, acc: List(Json)) -> Result(#(Json, P), ParseError) {
  case parse_value(p) {
    Error(e) -> Error(e)
    Ok(#(v, p2)) -> {
      let p2 = skip_ws(p2)
      case cur(p2) {
        "," -> parse_arr_items(skip_ws(advance(p2, 1)), [v, ..acc])
        _ -> Ok(#(JArr(list.reverse([v, ..acc])), case cur(p2) {
          "]" -> advance(p2, 1)
          _ -> p2
        }))
      }
    }
  }
}

fn parse_obj(p: P) -> Result(#(Json, P), ParseError) {
  let p = advance(p, 1)
  let p = skip_ws(p)
  case cur(p) {
    "}" -> Ok(#(JObj([]), advance(p, 1)))
    _ -> parse_obj_items(p, [])
  }
}

fn parse_obj_items(p: P, acc: List(#(String, Json))) -> Result(#(Json, P), ParseError) {
  let p = skip_ws(p)
  case parse_str(p) {
    Error(e) -> Error(e)
    Ok(#(key, p2)) -> {
      let p2 = skip_ws(p2)
      case cur(p2) {
        ":" -> {
          let p3 = skip_ws(advance(p2, 1))
          case parse_value(p3) {
            Error(e) -> Error(e)
            Ok(#(v, p4)) -> {
              let p4 = skip_ws(p4)
              let acc2 = [#(key, v), ..acc]
              case cur(p4) {
                "," -> parse_obj_items(skip_ws(advance(p4, 1)), acc2)
                "}" -> Ok(#(JObj(list.reverse(acc2)), advance(p4, 1)))
                _ -> Error(ParseError("expected , or }", p4.pos))
              }
            }
          }
        }
        _ -> Error(ParseError("expected :", p2.pos))
      }
    }
  }
}

// ---------- output ----------

fn escape_str(s: String) -> String {
  // minimal escaping
  s
  |> string.replace("\\", "\\\\")
  |> string.replace("\"", "\\\"")
  |> string.replace("\n", "\\n")
  |> string.replace("\t", "\\t")
  |> string.replace("\r", "\\r")
}

fn compact(j: Json) -> String {
  case j {
    JNull -> "null"
    JBool(True) -> "true"
    JBool(False) -> "false"
    JNum(n) -> n
    JStr(s) -> "\"" <> escape_str(s) <> "\""
    JArr(items) -> "[" <> join_compact(items, ",") <> "]"
    JObj(items) -> "{" <> join_obj_compact(items, ",") <> "}"
  }
}

fn join_compact(items: List(Json), sep: String) -> String {
  case items {
    [] -> ""
    [x] -> compact(x)
    [x, ..rest] -> compact(x) <> sep <> join_compact(rest, sep)
  }
}

fn join_obj_compact(items: List(#(String, Json)), sep: String) -> String {
  case items {
    [] -> ""
    [#(k, v)] -> "\"" <> escape_str(k) <> "\":" <> compact(v)
    [#(k, v), ..rest] -> "\"" <> escape_str(k) <> "\":" <> compact(v) <> sep <> join_obj_compact(rest, sep)
  }
}

fn pretty(j: Json) -> String {
  pretty_indent(j, 0)
}

fn pretty_indent(j: Json, depth: Int) -> String {
  let pad = string.repeat("  ", depth)
  let inner = string.repeat("  ", depth + 1)
  case j {
    JNull -> "null"
    JBool(True) -> "true"
    JBool(False) -> "false"
    JNum(n) -> n
    JStr(s) -> "\"" <> escape_str(s) <> "\""
    JArr([]) -> "[]"
    JArr(items) -> "[\n" <> inner <> pretty_items(items, inner, depth + 1) <> "\n" <> pad <> "]"
    JObj([]) -> "{}"
    JObj(items) -> "{\n" <> inner <> pretty_obj(items, inner, depth + 1) <> "\n" <> pad <> "}"
  }
}

fn pretty_items(items: List(Json), inner: String, depth: Int) -> String {
  case items {
    [] -> ""
    [x] -> pretty_indent(x, depth)
    [x, ..rest] -> pretty_indent(x, depth) <> ",\n" <> inner <> pretty_items(rest, inner, depth)
  }
}

fn pretty_obj(items: List(#(String, Json)), inner: String, depth: Int) -> String {
  case items {
    [] -> ""
    [#(k, v)] -> "\"" <> escape_str(k) <> "\": " <> pretty_indent(v, depth)
    [#(k, v), ..rest] -> "\"" <> escape_str(k) <> "\": " <> pretty_indent(v, depth) <> ",\n" <> inner <> pretty_obj(rest, inner, depth)
  }
}

// ---------- public ----------

pub fn parse_json(input: String) -> Result(Json, String) {
  case parse(P(input, 0)) {
    Ok(#(j, p)) -> {
      let p = skip_ws(p)
      case p.pos == string.length(p.input) {
        True -> Ok(j)
        False -> Error("trailing data")
      }
    }
    Error(e) -> Error(e.msg)
  }
}

pub fn to_compact(input: String) -> Result(String, String) {
  case parse_json(input) {
    Ok(j) -> Ok(compact(j))
    Error(e) -> Error(e)
  }
}

pub fn to_pretty(input: String) -> Result(String, String) {
  case parse_json(input) {
    Ok(j) -> Ok(pretty(j))
    Error(e) -> Error(e)
  }
}