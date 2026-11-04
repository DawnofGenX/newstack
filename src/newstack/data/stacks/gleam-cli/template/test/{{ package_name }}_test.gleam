import counts_test
import gleam/int
import gleam/io
import gleam/list
import options_test
import runner_test

/// Stop the VM with the given exit code so `gleam test` reports a failure.
@external(erlang, "erlang", "halt")
fn halt(code: Int) -> Nil

/// The test entry point. `gleam test` runs this: it runs every test module,
/// tallies the failures and exits non-zero if anything failed.
pub fn main() -> Nil {
  let results =
    list.append(
      list.append(counts_test.run(), options_test.run()),
      runner_test.run(),
    )
  // The harness returns "" for a passing check and the check's name for a
  // failing one, so filter the passes out before counting.
  let failures = list.filter(results, fn(name) { name != "" })
  let n = list.length(failures)
  case n > 0 {
    True -> {
      io.println_error("FAILED: " <> int.to_string(n) <> " test(s)")
      halt(1)
    }
    False -> io.println("All tests passed")
  }
}
