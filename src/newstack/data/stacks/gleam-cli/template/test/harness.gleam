import gleam/int
import gleam/io

/// Record an equality check on an Int. Returns the check name if it failed,
/// `""` if it passed. The caller collects the returned names into a list of
/// failures.
pub fn check_eq(name: String, actual: Int, expected: Int) -> String {
  case actual == expected {
    True -> {
      io.println("  ok: " <> name)
      ""
    }
    False -> {
      io.println(
        "  FAIL: "
        <> name
        <> " (expected "
        <> int.to_string(expected)
        <> ", got "
        <> int.to_string(actual)
        <> ")",
      )
      name
    }
  }
}

/// Record a boolean check. Returns the check name if it failed, `""` if it
/// passed.
pub fn check(name: String, ok: Bool) -> String {
  case ok {
    True -> {
      io.println("  ok: " <> name)
      ""
    }
    False -> {
      io.println("  FAIL: " <> name)
      name
    }
  }
}
