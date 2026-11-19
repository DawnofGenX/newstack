import gleam/int
import gleam/io
import gleam/list
import token_test

@external(erlang, "erlang", "halt")
fn halt(code: Int) -> Nil

pub fn main() -> Nil {
  let results = token_test.run()
  let failures = list.filter(results, fn(name) { name != "" })
  case list.length(failures) {
    0 -> io.println("All tests passed")
    n -> {
      io.println_error("FAILED: " <> int.to_string(n) <> " test(s)")
      halt(1)
    }
  }
}
