import gleam/string
import harness
import jwt/options
import jwt/token

pub fn run() -> List(String) {
  let claims = [#("sub", "alice"), #("iss", "demo")]
  let payload = token.encode_claims(claims)
  let signed = token.sign("whsec_test", token.default_header, payload)
  let pieces = string.split(signed, ".")
  [
    harness.check_eq(
      "claims encoding",
      payload,
      "{\"sub\":\"alice\",\"iss\":\"demo\"}",
    ),
    harness.check_int("three segments", list_len(pieces), 3),
    harness.check(
      "header segment",
      first(pieces) == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    ),
    harness.check(
      "round trip",
      token.verify("whsec_test", signed) == Ok(payload),
    ),
    harness.check("wrong secret", token.verify("wrong", signed) != Ok(payload)),
    harness.check(
      "malformed token",
      token.verify("whsec_test", "a.b")
        == Error("expected three dot-separated segments"),
    ),
    harness.check("claims decode", token.decode_claims(payload) == Ok(claims)),
    harness.check("non-object rejected", token.decode_claims("[1]") != Ok([])),
    harness.check_int(
      "usage error",
      case options.parse(["--bogus"]) {
        options.Parsed(options.UsageError(_), _) -> 2
        _ -> 0
      },
      2,
    ),
  ]
}

fn list_len(items: List(a)) -> Int {
  case items {
    [] -> 0
    [_, ..rest] -> 1 + list_len(rest)
  }
}

fn first(items: List(a)) -> a {
  case items {
    [value, ..] -> value
    [] -> panic as "empty list"
  }
}
