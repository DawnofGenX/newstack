/// A deliberately small HMAC-SHA256 JWT implementation: compact
/// base64url(header).base64url(payload).base64url(signature) with no third
/// party packages. Only flat JSON objects of string values are supported for
/// the payload helper, which keeps the encoder and decoder reviewable.
import gleam/bit_array
import gleam/list
import gleam/string

@external(erlang, "jwt_io", "b64url_encode")
fn b64url_encode(data: BitArray) -> String

@external(erlang, "jwt_io", "b64url_decode")
fn b64url_decode(text: String) -> BitArray

@external(erlang, "jwt_io", "hmac_sha256")
fn hmac_sha256(key: BitArray, data: BitArray) -> BitArray

pub const default_header = "{\"alg\":\"HS256\",\"typ\":\"JWT\"}"

/// Sign a header and payload with a shared secret.
pub fn sign(secret: String, header: String, payload: String) -> String {
  let encoded_header = b64url_encode(<<header:utf8>>)
  let encoded_payload = b64url_encode(<<payload:utf8>>)
  let signing_input = encoded_header <> "." <> encoded_payload
  let signature =
    b64url_encode(hmac_sha256(<<secret:utf8>>, <<signing_input:utf8>>))
  signing_input <> "." <> signature
}

/// Verify a token's signature and return its decoded payload.
pub fn verify(secret: String, token: String) -> Result(String, String) {
  case string.split(token, ".") {
    [header, payload, signature] -> {
      let expected =
        b64url_encode(
          hmac_sha256(<<secret:utf8>>, <<{ header <> "." <> payload }:utf8>>),
        )
      case expected == signature {
        False -> Error("signature mismatch")
        True ->
          case bit_array.to_string(b64url_decode(payload)) {
            Ok(text) -> Ok(text)
            Error(_) -> Error("payload is not UTF-8")
          }
      }
    }
    _ -> Error("expected three dot-separated segments")
  }
}

/// Encode a flat list of string claims as a compact JSON object. Keys are
/// emitted in insertion order; values are escaped for quotes and backslashes.
pub fn encode_claims(claims: List(#(String, String))) -> String {
  let pairs =
    list.map(claims, fn(pair) {
      "\"" <> escape(pair.0) <> "\":\"" <> escape(pair.1) <> "\""
    })
  "{" <> string.join(pairs, ",") <> "}"
}

fn escape(text: String) -> String {
  text
  |> string.replace("\\", "\\\\")
  |> string.replace("\"", "\\\"")
}

/// Decode a flat JSON object of string values. Returns an error on anything
/// outside that subset rather than pretending to be a general JSON parser.
pub fn decode_claims(text: String) -> Result(List(#(String, String)), String) {
  let trimmed = string.trim(text)
  case string.starts_with(trimmed, "{") && string.ends_with(trimmed, "}") {
    False -> Error("expected a JSON object")
    True -> {
      let body = string.slice(trimmed, 1, string.length(trimmed) - 2)
      case string.trim(body) == "" {
        True -> Ok([])
        False -> decode_pairs(string.split(body, ","), [])
      }
    }
  }
}

fn decode_pairs(
  parts: List(String),
  acc: List(#(String, String)),
) -> Result(List(#(String, String)), String) {
  case parts {
    [] -> Ok(list.reverse(acc))
    [part, ..rest] ->
      case string.split(part, ":") {
        [key, value] -> {
          let k = unquote(string.trim(key))
          let v = unquote(string.trim(value))
          case k == "" || string.contains(k, "\"") || v == "" {
            True -> Error("invalid claim pair")
            False -> decode_pairs(rest, [#(k, v), ..acc])
          }
        }
        _ -> Error("expected key:value pair")
      }
  }
}

fn unquote(text: String) -> String {
  case text {
    "\"" <> rest ->
      case string.ends_with(rest, "\"") {
        True -> string.slice(rest, 0, string.length(rest) - 1)
        False -> text
      }
    text -> text
  }
}
