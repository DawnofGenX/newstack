import gleeunit
import gleeunit/should
import json_parser as json

pub fn main() {
  gleeunit.main()
}

pub fn compact_known_test() {
  json.to_compact("{\"a\": 1, \"b\": [2, 3]}")
  |> should.equal(Ok("{\"a\":1,\"b\":[2,3]}"))
}

pub fn pretty_known_test() {
  json.to_pretty("{\"a\":1}")
  |> should.equal(Ok("{\n  \"a\": 1\n}"))
}

pub fn parse_error_test() {
  json.to_compact("{bad}")
  |> should.be_error()
}