import gleam/int
import gleam/io

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

pub fn check_eq(name: String, actual: String, expected: String) -> String {
  case actual == expected {
    True -> {
      io.println("  ok: " <> name)
      ""
    }
    False -> {
      io.println(
        "  FAIL: "
        <> name
        <> " expected ["
        <> expected
        <> "] got ["
        <> actual
        <> "]",
      )
      name
    }
  }
}

pub fn check_int(name: String, actual: Int, expected: Int) -> String {
  case actual == expected {
    True -> {
      io.println("  ok: " <> name)
      ""
    }
    False -> {
      io.println(
        "  FAIL: "
        <> name
        <> " expected "
        <> int.to_string(expected)
        <> " got "
        <> int.to_string(actual),
      )
      name
    }
  }
}
