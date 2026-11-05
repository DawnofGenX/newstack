import gleam/http.{Get, Post}
import gleam/string
import gleeunit
import gleeunit/should

import {{ package_name }}/contract
import {{ package_name }}/count

pub fn main() -> Nil {
  gleeunit.main()
}

pub fn empty_text_test() {
  count.count_text("")
  |> should.equal(count.Counts(lines: 0, words: 0, bytes: 0))
}

pub fn one_line_test() {
  count.count_text("hello world\n")
  |> should.equal(count.Counts(lines: 1, words: 2, bytes: 12))
}

pub fn blank_lines_are_lines_test() {
  count.count_text("\n\nx\n")
  |> should.equal(count.Counts(lines: 3, words: 1, bytes: 4))
}

pub fn whitespace_is_not_a_word_test() {
  count.count_text("  \t ")
  |> should.equal(count.Counts(lines: 0, words: 0, bytes: 4))
}

pub fn bytes_are_utf8_bytes_test() {
  count.count_text("héllo wörld\n")
  |> should.equal(count.Counts(lines: 1, words: 2, bytes: 14))
}

pub fn emoji_is_four_bytes_test() {
  count.count_text("🙂\n")
  |> should.equal(count.Counts(lines: 1, words: 1, bytes: 5))
}

pub fn health_test() {
  let reply = contract.route(Get, "/health", "", "")
  reply.status |> should.equal(200)
  reply.body |> should.equal("{\"status\":\"ok\"}")
}

pub fn get_stats_test() {
  let reply = contract.route(Get, "/stats", "text=hello+world%0A", "")
  reply.status |> should.equal(200)
  reply.body
  |> string.contains("\"text\":\"hello world\\n\"")
  |> should.be_true
  reply.body |> string.contains("\"lines\":1") |> should.be_true
  reply.body |> string.contains("\"words\":2") |> should.be_true
  reply.body |> string.contains("\"bytes\":12") |> should.be_true
}

pub fn get_stats_without_text_test() {
  let reply = contract.route(Get, "/stats", "", "")
  reply.status |> should.equal(422)
  reply.body |> string.contains("\"error\":\"missing_text\"") |> should.be_true
}

pub fn post_stats_test() {
  let reply = contract.route(Post, "/stats", "", "{\"text\":\"a b\\nc\\n\"}")
  reply.status |> should.equal(200)
  reply.body |> string.contains("\"lines\":2") |> should.be_true
  reply.body |> string.contains("\"words\":3") |> should.be_true
}

pub fn post_non_string_text_test() {
  let reply = contract.route(Post, "/stats", "", "{\"text\":42}")
  reply.status |> should.equal(422)
  reply.body |> string.contains("\"error\":\"missing_text\"") |> should.be_true
}

pub fn post_broken_json_test() {
  let reply = contract.route(Post, "/stats", "", "not json")
  reply.status |> should.equal(422)
  reply.body |> string.contains("\"error\":\"invalid_json\"") |> should.be_true
}

pub fn unknown_route_test() {
  let reply = contract.route(Get, "/nope", "", "")
  reply.status |> should.equal(404)
  reply.body |> string.contains("\"error\":\"not_found\"") |> should.be_true
  reply.body |> string.contains("no route for GET /nope") |> should.be_true
}

pub fn wrong_method_test() {
  let reply = contract.route(Post, "/health", "", "")
  reply.status |> should.equal(405)
  reply.body
  |> string.contains("\"error\":\"method_not_allowed\"")
  |> should.be_true
}
