let () =
  let open Harness in
  let read body = Json.read_text body in
  check_eq "plain string" (Json.Text "a b\nc\n") (read "{\"text\": \"a b\\nc\\n\"}");
  check_eq "number is missing" Json.Missing (read "{\"text\": 42}");
  check_eq "object has no text" Json.Missing (read "{}");
  check_eq "other key" Json.Missing (read "{\"other\": \"x\"}");
  check_eq "not json" Json.Invalid (read "nope");
  check_eq "empty body" Json.Invalid (read "");
  check_eq "array body" Json.Invalid (read "[\"text\"]");
  check_eq "trailing data" Json.Invalid (read "{\"text\": \"a\"} trailing");
  check_eq "unterminated" Json.Invalid (read "{\"text\": \"a");
  check_eq "escaped unicode" (Json.Text "aé") (read "{\"text\": \"a\\u00e9\"}");
  check_eq "surrogate pair" (Json.Text "🙂") (read "{\"text\": \"\\ud83d\\ude42\"}");
  check_eq "escaped quote" (Json.Text "say \"hi\"") (read "{\"text\": \"say \\\"hi\\\"\"}");
  finish ()
